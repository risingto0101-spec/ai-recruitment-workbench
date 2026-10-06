from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.db import get_connection
from app.services.matcher import refresh_matches_for_candidate

router = APIRouter()


@router.get("")
async def list_matches(
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(100, ge=1, le=1000),
):
    conn = get_connection()
    try:
        conditions = ["1=1"]
        params = []
        if candidate_id:
            conditions.append("m.candidate_id = ?")
            params.append(candidate_id)
        if job_id:
            conditions.append("m.job_id = ?")
            params.append(job_id)
        if min_score is not None:
            conditions.append("m.overall_score >= ?")
            params.append(min_score)
        sql = f"""
            SELECT m.*, c.name as candidate_name, c.status as candidate_status,
                   j.title as job_title, j.location as job_location
            FROM job_matches m
            JOIN candidates c ON m.candidate_id = c.id
            JOIN jobs j ON m.job_id = j.id
            WHERE {' AND '.join(conditions)}
            ORDER BY m.overall_score DESC
            LIMIT ?
        """
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return {"items": [dict(r) for r in rows]}
    finally:
        conn.close()


@router.get("/candidate/{candidate_id}")
async def get_candidate_matches(candidate_id: int):
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT m.*, j.title as job_title, j.location as job_location, j.status as job_status
            FROM job_matches m
            JOIN jobs j ON m.job_id = j.id
            WHERE m.candidate_id = ?
            ORDER BY m.overall_score DESC
            """,
            (candidate_id,),
        ).fetchall()
        return {"items": [dict(r) for r in rows]}
    finally:
        conn.close()


@router.post("/recalculate/{candidate_id}")
async def recalculate_matches(candidate_id: int):
    conn = get_connection()
    try:
        existing = conn.execute("SELECT id FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="候选人不存在")
    finally:
        conn.close()
    results = await refresh_matches_for_candidate(candidate_id)
    return {"candidate_id": candidate_id, "recalculated": True, "matches": len(results)}
