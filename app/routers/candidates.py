from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.db import get_connection, now_iso, to_json, from_json
from app.services.parser import parse_resume_text, parse_file
from app.services.matcher import refresh_matches_for_candidate

router = APIRouter()


class CandidateBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = ""
    email: Optional[str] = ""
    current_company: Optional[str] = ""
    current_title: Optional[str] = ""
    years_of_experience: Optional[float] = 0
    expected_salary_min: Optional[int] = 0
    expected_salary_max: Optional[int] = 0
    expected_location: Optional[str] = ""
    skills: Optional[List[str]] = []
    education: Optional[List[dict]] = []
    work_history: Optional[List[dict]] = []
    raw_text: Optional[str] = ""
    source: Optional[str] = "manual"
    status: Optional[str] = "new"
    intended_job_id: Optional[int] = None
    notes: Optional[str] = ""


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    years_of_experience: Optional[float] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    expected_location: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[List[dict]] = None
    work_history: Optional[List[dict]] = None
    raw_text: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    intended_job_id: Optional[int] = None
    notes: Optional[str] = None


class ParseTextRequest(BaseModel):
    text: str = Field(min_length=10)


def _candidate_row_to_dict(row) -> dict:
    d = dict(row)
    d["skills"] = from_json(d.get("skills"), [])
    d["education"] = from_json(d.get("education"), [])
    d["work_history"] = from_json(d.get("work_history"), [])
    return d


def _insert_candidate(conn, data: dict) -> int:
    t = now_iso()
    cur = conn.execute(
        """
        INSERT INTO candidates (name, phone, email, current_company, current_title,
            years_of_experience, expected_salary_min, expected_salary_max, expected_location,
            skills, education, work_history, raw_text, source, status, intended_job_id,
            status_updated_at, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["name"], data["phone"], data["email"], data["current_company"], data["current_title"],
            data["years_of_experience"], data["expected_salary_min"], data["expected_salary_max"],
            data["expected_location"], to_json(data["skills"]), to_json(data["education"]),
            to_json(data["work_history"]), data["raw_text"], data["source"], data["status"],
            data.get("intended_job_id"), t, data.get("notes", ""), t, t,
        ),
    )
    return cur.lastrowid


def _update_candidate_sql(data: dict) -> tuple:
    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    values = []
    for k, v in data.items():
        if k in ("skills", "education", "work_history"):
            values.append(to_json(v))
        else:
            values.append(v)
    return set_clause, values


@router.get("")
async def list_candidates(
    status: Optional[str] = None,
    source: Optional[str] = None,
    job_id: Optional[int] = None,
    q: Optional[str] = None,
    min_score: Optional[float] = None,
):
    conn = get_connection()
    try:
        conditions = ["1=1"]
        params = []
        if status:
            conditions.append("c.status = ?")
            params.append(status)
        if source:
            conditions.append("c.source = ?")
            params.append(source)
        if job_id:
            conditions.append("c.intended_job_id = ?")
            params.append(job_id)
        if q:
            conditions.append("(c.name LIKE ? OR c.current_company LIKE ? OR c.current_title LIKE ?)")
            params.extend([f"%{q}%"] * 3)
        if min_score is not None:
            conditions.append("COALESCE(best.overall_score, 0) >= ?")
            params.append(min_score)
        sql = f"""
            SELECT c.*,
                   best.job_id as best_job_id, best.job_title as best_job_title,
                   best.overall_score as best_score
            FROM candidates c
            LEFT JOIN (
                SELECT m.candidate_id, m.job_id, m.overall_score, j.title as job_title
                FROM job_matches m
                JOIN jobs j ON m.job_id = j.id
                WHERE (m.candidate_id, m.overall_score) IN (
                    SELECT candidate_id, MAX(overall_score) FROM job_matches GROUP BY candidate_id
                )
            ) best ON best.candidate_id = c.id
            WHERE {' AND '.join(conditions)}
            ORDER BY c.updated_at DESC
        """
        rows = conn.execute(sql, params).fetchall()
        items = []
        for r in rows:
            d = _candidate_row_to_dict(r)
            d["best_job_id"] = r["best_job_id"]
            d["best_job_title"] = r["best_job_title"]
            d["best_score"] = r["best_score"]
            items.append(d)
        return {"items": items}
    finally:
        conn.close()


@router.post("")
async def create_candidate(candidate: CandidateCreate):
    conn = get_connection()
    try:
        candidate_id = _insert_candidate(conn, candidate.model_dump())
        conn.commit()
        await refresh_matches_for_candidate(candidate_id)
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        return _candidate_row_to_dict(row)
    finally:
        conn.close()


@router.get("/{candidate_id}")
async def get_candidate(candidate_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="候选人不存在")
        return _candidate_row_to_dict(row)
    finally:
        conn.close()


@router.put("/{candidate_id}")
async def update_candidate(candidate_id: int, candidate: CandidateUpdate):
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="候选人不存在")
        data = candidate.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(status_code=400, detail="没有可更新的字段")
        # 状态变更时更新时间戳
        if "status" in data:
            data["status_updated_at"] = now_iso()
        set_clause, values = _update_candidate_sql(data)
        values.append(now_iso())
        values.append(candidate_id)
        conn.execute(f"UPDATE candidates SET {set_clause}, updated_at = ? WHERE id = ?", values)
        conn.commit()
        # 如果影响匹配相关的字段发生变化，重新匹配
        match_keys = {"skills", "years_of_experience", "expected_salary_min", "expected_salary_max", "expected_location", "intended_job_id"}
        if match_keys & set(data.keys()):
            await refresh_matches_for_candidate(candidate_id)
        row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        return _candidate_row_to_dict(row)
    finally:
        conn.close()


@router.delete("/{candidate_id}")
async def delete_candidate(candidate_id: int):
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="候选人不存在")
        conn.execute("DELETE FROM job_matches WHERE candidate_id = ?", (candidate_id,))
        conn.execute("DELETE FROM candidates WHERE id = ?", (candidate_id,))
        conn.commit()
        return {"id": candidate_id, "deleted": True}
    finally:
        conn.close()


@router.post("/parse-text")
async def parse_candidate_text_route(req: ParseTextRequest):
    try:
        parsed = await parse_resume_text(req.text)
        return {"parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_candidate_file(file: UploadFile = File(...), source: str = Form("upload")):
    try:
        parsed = await parse_file(file, source=source)
        conn = get_connection()
        try:
            candidate_id = _insert_candidate(conn, parsed)
            conn.commit()
            await refresh_matches_for_candidate(candidate_id)
            row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
            return {"filename": file.filename, "candidate": _candidate_row_to_dict(row)}
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/from-parsed")
async def create_from_parsed(candidate: CandidateCreate):
    """从解析结果直接保存候选人"""
    return await create_candidate(candidate)
