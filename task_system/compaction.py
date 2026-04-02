from collections import Counter
from datetime import datetime, timezone

from .log import append_event
from .index import _conn
from .search import add_revision as search_add

def compact(every_n: int = 10) -> bool:
    with _conn() as con:
        total = con.execute(
            "SELECT COUNT(*) as n FROM agent_tasks WHERE status IN ('done','failed')"
        ).fetchone()["n"]

    if total == 0 or total % every_n != 0:
        return False

    with _conn() as con:
        rows = con.execute(
            "SELECT t.status, r.error_type FROM agent_tasks t "
            "JOIN agent_task_revisions r ON t.task_id=r.task_id AND t.current_revision=r.revision"
        ).fetchall()

    status_counts = Counter(r["status"] for r in rows)
    error_counts  = Counter(r["error_type"] for r in rows if r["error_type"])
    top_errors    = [e for e, _ in error_counts.most_common(3)]

    ts         = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    compact_id = f"COMPACT_{ts}"
    summary    = (
        f"Compaction at {total} closed tasks. "
        f"done={status_counts.get('done', 0)} "
        f"failed={status_counts.get('failed', 0)} "
        f"top_errors={top_errors}"
    )
    append_event(compact_id, 0, "system", "compact",
                 {"total": total, "status_counts": dict(status_counts),
                  "top_errors": top_errors})
    search_add(compact_id, 0, "compact", summary)
    return True
