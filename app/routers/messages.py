from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_connection
from app.services.message_generator import generate_message

router = APIRouter()


class GenerateMessageRequest(BaseModel):
    candidate_id: int
    job_id: int
    category: str


@router.post("/generate")
async def generate_message_route(req: GenerateMessageRequest):
    conn = get_connection()
    try:
        candidate_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (req.candidate_id,)).fetchone()
        if not candidate_row:
            raise HTTPException(status_code=404, detail="候选人不存在")
        job_row = conn.execute("SELECT * FROM jobs WHERE id = ?", (req.job_id,)).fetchone()
        if not job_row:
            raise HTTPException(status_code=404, detail="岗位不存在")
        candidate = dict(candidate_row)
        job = dict(job_row)
        message = generate_message(candidate, job, req.category)
        return {"message": message}
    finally:
        conn.close()


@router.get("/templates")
async def list_templates():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM message_templates ORDER BY category, id").fetchall()
        return {"items": [dict(r) for r in rows]}
    finally:
        conn.close()
