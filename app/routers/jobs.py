from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.db import get_connection, now_iso, to_json, from_json
from app.services.parser import parse_job_text

router = APIRouter()


class JobBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    department: Optional[str] = ""
    location: Optional[str] = ""
    salary_min: Optional[int] = 0
    salary_max: Optional[int] = 0
    currency: Optional[str] = "CNY"
    description: Optional[str] = ""
    requirements: Optional[str] = ""
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    min_years: Optional[int] = 0
    max_years: Optional[int] = 0
    status: Optional[str] = "open"


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_years: Optional[int] = None
    max_years: Optional[int] = None
    status: Optional[str] = None


class ParseJobRequest(BaseModel):
    text: str = Field(min_length=10)


def _job_row_to_dict(row) -> dict:
    d = dict(row)
    d["required_skills"] = from_json(d.get("required_skills"), [])
    d["preferred_skills"] = from_json(d.get("preferred_skills"), [])
    return d


@router.get("")
async def list_jobs(status: Optional[str] = None):
    conn = get_connection()
    try:
        if status:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE status = ? ORDER BY updated_at DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM jobs ORDER BY updated_at DESC").fetchall()
        return {"items": [_job_row_to_dict(r) for r in rows]}
    finally:
        conn.close()


@router.post("")
async def create_job(job: JobCreate):
    conn = get_connection()
    try:
        t = now_iso()
        cur = conn.execute(
            """
            INSERT INTO jobs (title, department, location, salary_min, salary_max, currency,
                description, requirements, required_skills, preferred_skills, min_years,
                max_years, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.title, job.department, job.location, job.salary_min, job.salary_max,
                job.currency, job.description, job.requirements,
                to_json(job.required_skills), to_json(job.preferred_skills),
                job.min_years, job.max_years, job.status, t, t,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _job_row_to_dict(row)
    finally:
        conn.close()


@router.get("/{job_id}")
async def get_job(job_id: int):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="岗位不存在")
        return _job_row_to_dict(row)
    finally:
        conn.close()


@router.put("/{job_id}")
async def update_job(job_id: int, job: JobUpdate):
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="岗位不存在")
        data = job.model_dump(exclude_unset=True)
        if not data:
            raise HTTPException(status_code=400, detail="没有可更新的字段")
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        values = []
        for k, v in data.items():
            if k in ("required_skills", "preferred_skills"):
                values.append(to_json(v))
            else:
                values.append(v)
        values.append(now_iso())
        values.append(job_id)
        conn.execute(f"UPDATE jobs SET {set_clause}, updated_at = ? WHERE id = ?", values)
        conn.commit()
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_row_to_dict(row)
    finally:
        conn.close()


@router.delete("/{job_id}")
async def delete_job(job_id: int):
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="岗位不存在")
        conn.execute("DELETE FROM job_matches WHERE job_id = ?", (job_id,))
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        return {"id": job_id, "deleted": True}
    finally:
        conn.close()


@router.post("/parse")
async def parse_job_text_route(req: ParseJobRequest):
    try:
        parsed = await parse_job_text(req.text)
        return {"parsed": parsed}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
