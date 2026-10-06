from typing import Dict, Any, Optional
from fastapi import UploadFile

from app.services.ai_client import get_ai_client
from app.services.rule_engine import parse_job, parse_resume


async def parse_job_text(text: str) -> Dict[str, Any]:
    """解析 JD 文本，优先 AI，失败降级规则引擎"""
    text = (text or "").strip()
    if not text:
        raise ValueError("JD 文本不能为空")

    ai_client = get_ai_client()
    if ai_client.available():
        parsed = await ai_client.parse_job(text)
        if parsed:
            return _normalize_job(parsed)
    return _normalize_job(parse_job(text))


async def parse_resume_text(text: str, source: str = "manual") -> Dict[str, Any]:
    """解析简历文本，优先 AI，失败降级规则引擎"""
    text = (text or "").strip()
    if not text:
        raise ValueError("简历文本不能为空")

    ai_client = get_ai_client()
    if ai_client.available():
        parsed = await ai_client.parse_resume(text)
        if parsed:
            return _normalize_resume(parsed, source)
    return _normalize_resume(parse_resume(text), source)


async def parse_file(file: UploadFile, source: str = "upload") -> Dict[str, Any]:
    """根据文件类型解析简历"""
    filename = (file.filename or "").lower()
    content = await file.read()

    if filename.endswith(".pdf"):
        text = _extract_pdf_text(content)
    elif filename.endswith(".docx") or filename.endswith(".doc"):
        text = _extract_docx_text(content)
    elif filename.endswith(".txt"):
        text = content.decode("utf-8", errors="ignore")
    else:
        # 尝试按文本读取
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

    if not text or not text.strip():
        raise ValueError("无法从文件中提取文本")

    return await parse_resume_text(text, source=source)


def _extract_pdf_text(content: bytes) -> str:
    import io
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return "\n".join(text_parts)


def _extract_docx_text(content: bytes) -> str:
    import io
    from docx import Document
    doc = Document(io.BytesIO(content))
    text_parts = []
    for para in doc.paragraphs:
        text_parts.append(para.text)
    return "\n".join(text_parts)


def _to_list(value: Any) -> list:
    if isinstance(value, list):
        return [str(v) for v in value if v]
    if isinstance(value, str):
        return [v.strip() for v in value.split(",") if v.strip()]
    return []


def _normalize_job(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "title": str(data.get("title") or "未命名岗位")[:200],
        "department": str(data.get("department") or "")[:100],
        "location": str(data.get("location") or "")[:100],
        "salary_min": int(data.get("salary_min") or 0),
        "salary_max": int(data.get("salary_max") or 0),
        "currency": str(data.get("currency") or "CNY")[:10],
        "description": str(data.get("description") or ""),
        "requirements": str(data.get("requirements") or data.get("description") or ""),
        "required_skills": _to_list(data.get("required_skills")),
        "preferred_skills": _to_list(data.get("preferred_skills")),
        "min_years": int(data.get("min_years") or 0),
        "max_years": int(data.get("max_years") or 0),
        "status": str(data.get("status") or "open").lower()[:20],
        "parsed_by": data.get("parsed_by", "unknown"),
    }


def _normalize_resume(data: Dict[str, Any], source: str) -> Dict[str, Any]:
    return {
        "name": str(data.get("name") or "未命名候选人")[:100],
        "phone": str(data.get("phone") or "")[:50],
        "email": str(data.get("email") or "")[:100],
        "current_company": str(data.get("current_company") or "")[:100],
        "current_title": str(data.get("current_title") or "")[:100],
        "years_of_experience": float(data.get("years_of_experience") or 0),
        "expected_salary_min": int(data.get("expected_salary_min") or 0),
        "expected_salary_max": int(data.get("expected_salary_max") or 0),
        "expected_location": str(data.get("expected_location") or "")[:100],
        "skills": _to_list(data.get("skills")),
        "education": data.get("education") if isinstance(data.get("education"), list) else [],
        "work_history": data.get("work_history") if isinstance(data.get("work_history"), list) else [],
        "raw_text": str(data.get("raw_text") or ""),
        "source": source,
        "status": str(data.get("status") or "new").lower()[:20],
        "intended_job_id": int(data.get("intended_job_id") or 0) or None,
        "notes": str(data.get("notes") or ""),
        "parsed_by": data.get("parsed_by", "unknown"),
    }
