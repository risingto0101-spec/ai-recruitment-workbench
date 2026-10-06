from fastapi import APIRouter
from datetime import datetime, timezone, timedelta

from app.db import get_connection

router = APIRouter()


@router.get("")
async def dashboard_stats():
    conn = get_connection()
    try:
        total_jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        open_jobs = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'open'").fetchone()[0]
        total_candidates = conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0]

        status_rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM candidates GROUP BY status"
        ).fetchall()
        status_counts = {r["status"]: r["cnt"] for r in status_rows}

        # 近 7 天新增
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        recent_candidates = conn.execute(
            "SELECT COUNT(*) FROM candidates WHERE created_at > ?", (seven_days_ago,)
        ).fetchone()[0]
        recent_jobs = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE created_at > ?", (seven_days_ago,)
        ).fetchone()[0]

        # 待跟进：超过 7 天未更新状态且不在已入职/已拒绝
        follow_up_threshold = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        follow_up = conn.execute(
            """
            SELECT COUNT(*) FROM candidates
            WHERE status_updated_at < ? AND status NOT IN ('hired', 'rejected')
            """,
            (follow_up_threshold,),
        ).fetchone()[0]

        # 平均匹配分
        avg_score = conn.execute(
            "SELECT AVG(overall_score) FROM job_matches"
        ).fetchone()[0] or 0

        return {
            "total_jobs": total_jobs,
            "open_jobs": open_jobs,
            "total_candidates": total_candidates,
            "status_counts": status_counts,
            "recent_candidates": recent_candidates,
            "recent_jobs": recent_jobs,
            "follow_up": follow_up,
            "avg_match_score": round(avg_score, 1),
        }
    finally:
        conn.close()
