from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.db import get_connection
from app.services.parser import parse_resume_text
from app.services.matcher import refresh_matches_for_candidate
from app.routers.candidates import _insert_candidate, _candidate_row_to_dict

router = APIRouter()


class ExtensionPushRequest(BaseModel):
    source: str = Field(..., pattern="^(boss|51job|manual)$")
    url: str = ""
    title: str = ""
    content: str = Field(..., min_length=10)
    html: str = ""


@router.post("/push")
async def push_from_extension(req: ExtensionPushRequest):
    try:
        # 优先使用 title 作为候选人姓名或辅助信息
        text = req.content
        if req.title:
            text = req.title + "\n" + text
        parsed = await parse_resume_text(text, source=req.source)
        conn = get_connection()
        try:
            candidate_id = _insert_candidate(conn, parsed)
            conn.commit()
            await refresh_matches_for_candidate(candidate_id)
            row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
            return {"received": True, "candidate": _candidate_row_to_dict(row)}
        finally:
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
