from typing import Dict, Any, List

from app.db import get_connection, now_iso
from app.services.ai_client import get_ai_client
from app.services.rule_engine import calculate_match as rule_calculate_match


async def calculate_match(candidate: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
    """计算单候选人与单岗位的匹配分数，优先 AI，失败降级规则引擎"""
    ai_client = get_ai_client()
    if ai_client.available():
        try:
            parsed = await ai_client.match(candidate, job)
            if parsed and "overall_score" in parsed:
                return _normalize_match(parsed)
        except Exception:
            pass
    return rule_calculate_match(candidate, job)


def _normalize_match(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "skill_score": float(data.get("skill_score") or 0),
        "experience_score": float(data.get("experience_score") or 0),
        "salary_score": float(data.get("salary_score") or 0),
        "location_score": float(data.get("location_score") or 0),
        "overall_score": float(data.get("overall_score") or 0),
        "reason": str(data.get("reason") or ""),
    }


async def refresh_matches_for_candidate(candidate_id: int) -> List[Dict[str, Any]]:
    """为指定候选人重新计算与全部 open 岗位的匹配"""
    conn = get_connection()
    try:
        # 读取候选人
        row = conn.execute(
            "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
        ).fetchone()
        if not row:
            return []
        candidate = _row_to_candidate(row)

        # 读取开放岗位
        jobs = conn.execute("SELECT * FROM jobs WHERE status = 'open'").fetchall()

        results = []
        for job_row in jobs:
            job = _row_to_job(job_row)
            match_data = await calculate_match(candidate, job)
            conn.execute(
                """
                INSERT INTO job_matches
                (candidate_id, job_id, skill_score, experience_score, salary_score, location_score, overall_score, reason, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(candidate_id, job_id) DO UPDATE SET
                    skill_score=excluded.skill_score,
                    experience_score=excluded.experience_score,
                    salary_score=excluded.salary_score,
                    location_score=excluded.location_score,
                    overall_score=excluded.overall_score,
                    reason=excluded.reason,
                    updated_at=excluded.updated_at
                """,
                (
                    candidate_id,
                    job["id"],
                    match_data["skill_score"],
                    match_data["experience_score"],
                    match_data["salary_score"],
                    match_data["location_score"],
                    match_data["overall_score"],
                    match_data["reason"],
                    now_iso(),
                    now_iso(),
                ),
            )
            results.append({"job_id": job["id"], **match_data})
        conn.commit()
        return results
    finally:
        conn.close()


def _row_to_candidate(row: Any) -> Dict[str, Any]:
    import json
    candidate = dict(row)
    for key in ["skills", "education", "work_history"]:
        val = candidate.get(key)
        if isinstance(val, str):
            try:
                candidate[key] = json.loads(val)
            except Exception:
                candidate[key] = []
        else:
            candidate[key] = val or []
    return candidate


def _row_to_job(row: Any) -> Dict[str, Any]:
    import json
    job = dict(row)
    for key in ["required_skills", "preferred_skills"]:
        val = job.get(key)
        if isinstance(val, str):
            try:
                job[key] = json.loads(val)
            except Exception:
                job[key] = []
        else:
            job[key] = val or []
    return job
