import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from . import config

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agent_tasks (
    task_id          TEXT PRIMARY KEY,
    current_revision INTEGER NOT NULL DEFAULT 1,
    status           TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS agent_task_revisions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id         TEXT    NOT NULL REFERENCES agent_tasks(task_id),
    revision        INTEGER NOT NULL,
    parent_revision INTEGER,
    status          TEXT    NOT NULL,
    summary         TEXT    NOT NULL,
    spec            TEXT,
    error_type      TEXT,
    fix_strategy    TEXT,
    actor           TEXT    NOT NULL,
    created_at      TEXT    NOT NULL,
    UNIQUE(task_id, revision)
);
"""

@contextmanager
def _conn():
    con = sqlite3.connect(str(config.DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def ensure_schema() -> None:
    with _conn() as con:
        con.executescript(SCHEMA_SQL)

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def insert_task(task_id: str, summary: str, spec: str, actor: str) -> None:
    now = _now()
    with _conn() as con:
        con.execute(
            "INSERT INTO agent_tasks (task_id, current_revision, status, created_at, updated_at) "
            "VALUES (?, 1, 'pending', ?, ?)",
            (task_id, now, now)
        )
        con.execute(
            "INSERT INTO agent_task_revisions "
            "(task_id, revision, parent_revision, status, summary, spec, error_type, fix_strategy, actor, created_at) "
            "VALUES (?, 1, NULL, 'pending', ?, ?, NULL, NULL, ?, ?)",
            (task_id, summary, spec, actor, now)
        )

def update_task_status(task_id: str, status: str) -> None:
    with _conn() as con:
        row = con.execute(
            "SELECT current_revision FROM agent_tasks WHERE task_id=?",
            (task_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"task_id not found: {task_id}")
        con.execute(
            "UPDATE agent_tasks SET status=?, updated_at=? WHERE task_id=?",
            (status, _now(), task_id)
        )
        con.execute(
            "UPDATE agent_task_revisions SET status=? WHERE task_id=? AND revision=?",
            (status, task_id, row["current_revision"])
        )

def insert_correction_revision(task_id: str, summary: str, spec: str | None,
                                error_type: str, fix_strategy: str, actor: str) -> int:
    with _conn() as con:
        row = con.execute(
            "SELECT current_revision FROM agent_tasks WHERE task_id=?", (task_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"task_id not found: {task_id}")
        parent_rev = row["current_revision"]
        new_rev = parent_rev + 1
        now = _now()
        if spec is None:
            parent_row = con.execute(
                "SELECT spec FROM agent_task_revisions WHERE task_id=? AND revision=?",
                (task_id, parent_rev)
            ).fetchone()
            spec = parent_row["spec"] if parent_row else None
        con.execute(
            "INSERT INTO agent_task_revisions "
            "(task_id, revision, parent_revision, status, summary, spec, error_type, fix_strategy, actor, created_at) "
            "VALUES (?, ?, ?, 'correcting', ?, ?, ?, ?, ?, ?)",
            (task_id, new_rev, parent_rev, summary, spec, error_type, fix_strategy, actor, now)
        )
        con.execute(
            "UPDATE agent_tasks SET current_revision=?, status='correcting', updated_at=? WHERE task_id=?",
            (new_rev, now, task_id)
        )
        return new_rev

def get_task(task_id: str) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM agent_tasks WHERE task_id=?", (task_id,)
        ).fetchone()
        return dict(row) if row else None

def get_task_with_spec(task_id: str) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT t.task_id, t.current_revision, t.status, t.created_at, t.updated_at, "
            "r.summary, r.spec "
            "FROM agent_tasks t "
            "JOIN agent_task_revisions r ON t.task_id=r.task_id AND t.current_revision=r.revision "
            "WHERE t.task_id=?",
            (task_id,)
        ).fetchone()
        return dict(row) if row else None

def get_next_pending() -> dict | None:
    """Return the oldest pending task with its full current spec."""
    with _conn() as con:
        row = con.execute(
            "SELECT t.task_id, t.current_revision, t.status, t.created_at, "
            "r.summary, r.spec "
            "FROM agent_tasks t "
            "JOIN agent_task_revisions r ON t.task_id=r.task_id AND t.current_revision=r.revision "
            "WHERE t.status='pending' "
            "ORDER BY t.created_at ASC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

def get_revisions(task_id: str) -> list:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM agent_task_revisions WHERE task_id=? ORDER BY revision",
            (task_id,)
        ).fetchall()
        return [dict(r) for r in rows]
