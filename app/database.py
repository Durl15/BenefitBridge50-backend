from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import AssessmentRecord

DB_PATH = Path(os.getenv("DATABASE_URL", "sqlite:///./benefitbridge.db").replace("sqlite:///", ""))


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                user_alias_hash TEXT NOT NULL,
                state TEXT NOT NULL,
                county TEXT,
                input_json TEXT NOT NULL,
                matches_json TEXT NOT NULL,
                risk_flags_json TEXT NOT NULL
            )
            """
        )
        conn.commit()


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_assessment(record: AssessmentRecord) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO assessments (id, created_at, user_alias_hash, state, county, input_json, matches_json, risk_flags_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.id,
                record.created_at,
                record.user_alias_hash,
                record.state,
                record.county,
                json.dumps(record.input_json),
                json.dumps(record.matches_json),
                json.dumps(record.risk_flags_json),
            ),
        )


def load_assessment(assessment_id: str) -> AssessmentRecord | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM assessments WHERE id = ?", (assessment_id,)).fetchone()
    if row is None:
        return None
    return AssessmentRecord(
        id=row["id"],
        created_at=row["created_at"],
        user_alias_hash=row["user_alias_hash"],
        state=row["state"],
        county=row["county"],
        input_json=json.loads(row["input_json"]),
        matches_json=json.loads(row["matches_json"]),
        risk_flags_json=json.loads(row["risk_flags_json"]),
    )


def list_assessments(limit: int = 25) -> list[AssessmentRecord]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM assessments ORDER BY created_at DESC LIMIT ?",
            (max(1, min(limit, 100)),),
        ).fetchall()
    return [
        AssessmentRecord(
            id=row["id"],
            created_at=row["created_at"],
            user_alias_hash=row["user_alias_hash"],
            state=row["state"],
            county=row["county"],
            input_json=json.loads(row["input_json"]),
            matches_json=json.loads(row["matches_json"]),
            risk_flags_json=json.loads(row["risk_flags_json"]),
        )
        for row in rows
    ]
