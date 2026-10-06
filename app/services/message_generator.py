from typing import Dict, Any

from app.db import get_connection


def generate_message(candidate: Dict[str, Any], job: Dict[str, Any], category: str) -> str:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT content FROM message_templates WHERE category = ? ORDER BY id LIMIT 1",
            (category,),
        ).fetchone()
        template = row[0] if row else ""
    finally:
        conn.close()

    if not template:
        template = "{{name}} 您好，关于 {{job_title}} 岗位，想跟您进一步沟通。"

    return (
        template
        .replace("{{name}}", candidate.get("name") or "")
        .replace("{{job_title}}", job.get("title") or "")
        .replace("{{company}}", candidate.get("current_company") or "")
        .replace("{{location}}", job.get("location") or "")
        .replace("{{phone}}", candidate.get("phone") or "")
        .replace("{{email}}", candidate.get("email") or "")
    )
