import sqlite3
import json
from datetime import datetime, timezone
from typing import Any, Optional

from app.config import DB_PATH


INIT_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department TEXT DEFAULT '',
    location TEXT DEFAULT '',
    salary_min INTEGER DEFAULT 0,
    salary_max INTEGER DEFAULT 0,
    currency TEXT DEFAULT 'CNY',
    description TEXT DEFAULT '',
    requirements TEXT DEFAULT '',
    required_skills TEXT DEFAULT '[]',
    preferred_skills TEXT DEFAULT '[]',
    min_years INTEGER DEFAULT 0,
    max_years INTEGER DEFAULT 0,
    status TEXT DEFAULT 'open',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT DEFAULT '',
    email TEXT DEFAULT '',
    current_company TEXT DEFAULT '',
    current_title TEXT DEFAULT '',
    years_of_experience REAL DEFAULT 0,
    expected_salary_min INTEGER DEFAULT 0,
    expected_salary_max INTEGER DEFAULT 0,
    expected_location TEXT DEFAULT '',
    skills TEXT DEFAULT '[]',
    education TEXT DEFAULT '[]',
    work_history TEXT DEFAULT '[]',
    raw_text TEXT DEFAULT '',
    source TEXT DEFAULT 'manual',
    status TEXT DEFAULT 'new',
    intended_job_id INTEGER DEFAULT NULL,
    status_updated_at TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (intended_job_id) REFERENCES jobs(id)
);

CREATE TABLE IF NOT EXISTS job_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    job_id INTEGER NOT NULL,
    skill_score REAL DEFAULT 0,
    experience_score REAL DEFAULT 0,
    salary_score REAL DEFAULT 0,
    location_score REAL DEFAULT 0,
    overall_score REAL DEFAULT 0,
    reason TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(candidate_id, job_id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS message_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    content TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_intended_job ON candidates(intended_job_id);
CREATE INDEX IF NOT EXISTS idx_matches_candidate ON job_matches(candidate_id);
CREATE INDEX IF NOT EXISTS idx_matches_job ON job_matches(job_id);
CREATE INDEX IF NOT EXISTS idx_matches_overall ON job_matches(overall_score);
"""

DEFAULT_TEMPLATES = [
    ("面试邀请", "interview", "{{name}} 您好，我是 {{company}} 的 HR。您的简历与我们的 {{job_title}} 岗位非常匹配，想邀请您参加进一步的沟通/面试。请问您最近什么时候方便？"),
    ("不合适婉拒", "reject", "{{name}} 您好，感谢您对 {{job_title}} 岗位的关注。经过评估，目前您的履历与该岗位匹配度不够高，期待未来有机会再合作。"),
    ("跟进提醒", "follow", "{{name}} 您好，之前跟您沟通过 {{job_title}} 岗位，想跟进一下您目前的考虑，请问是否还有意向？"),
    ("初次联系", "invite", "{{name}} 您好，看到您的履历与 {{job_title}} 岗位比较匹配，想和您初步沟通一下，请问是否方便？"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(INIT_SQL)
        # 插入默认话术模板
        existing = conn.execute("SELECT COUNT(*) FROM message_templates").fetchone()[0]
        if existing == 0:
            for name, category, content in DEFAULT_TEMPLATES:
                conn.execute(
                    "INSERT INTO message_templates (name, category, content, created_at) VALUES (?, ?, ?, ?)",
                    (name, category, content, now_iso()),
                )
        conn.commit()
    finally:
        conn.close()


def to_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def from_json(text: Optional[str], default: Any = None) -> Any:
    if not text:
        return default if default is not None else []
    try:
        return json.loads(text)
    except Exception:
        return default if default is not None else []
