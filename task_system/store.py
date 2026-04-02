from .log import append_event
from . import index as idx
from . import search as srch
from .compaction import compact as _compact


class TaskStore:
    """Three-layer versioned task store for agent-driven workflows."""

    def __init__(self):
        idx.ensure_schema()

    # Write
    def create_task(self, task_id: str, summary: str, spec: str,
                    actor: str = "architect") -> None:
        idx.insert_task(task_id, summary, spec, actor)
        append_event(task_id, 1, actor, "create", {"summary": summary})
        srch.add_revision(task_id, 1, "pending", summary)

    def execute_task(self, task_id: str, result: str,
                     actor: str = "executor") -> None:
        idx.update_task_status(task_id, "executing")
        task = idx.get_task(task_id)
        rev = task["current_revision"]
        append_event(task_id, rev, actor, "execute", {"result": result})
        srch.add_revision(task_id, rev, "executing", result)

    def audit_task(self, task_id: str, findings: str, status: str,
                   actor: str = "architect") -> None:
        """status: 'done' | 'needs_fix'"""
        resolved = "done" if status == "done" else "failed"
        idx.update_task_status(task_id, resolved)
        task = idx.get_task(task_id)
        rev = task["current_revision"]
        append_event(task_id, rev, actor, "audit", {"findings": findings, "status": status})
        srch.add_revision(task_id, rev, resolved, findings)

    def correct_task(self, task_id: str, fix_strategy: str, error_type: str,
                     spec: str = None, actor: str = "architect") -> None:
        """Create a new revision chained to the previous one."""
        new_rev = idx.insert_correction_revision(
            task_id, fix_strategy, spec, error_type, fix_strategy, actor
        )
        append_event(task_id, new_rev, actor, "correct",
                     {"fix_strategy": fix_strategy, "error_type": error_type})
        srch.add_revision(task_id, new_rev, "correcting",
                          f"[{error_type}] {fix_strategy}")

    # Read
    def get_next_pending(self) -> dict | None:
        """Return the oldest pending task with its current spec."""
        return idx.get_next_pending()

    def get_task_with_spec(self, task_id: str) -> dict | None:
        return idx.get_task_with_spec(task_id)

    def get_task(self, task_id: str) -> dict | None:
        return idx.get_task(task_id)

    def get_history(self, task_id: str) -> list:
        return idx.get_revisions(task_id)

    def search(self, query: str, top_k: int = 5) -> list:
        return srch.search(query, top_k)

    # Maintenance
    def maybe_compact(self, every_n: int = 10) -> bool:
        return _compact(every_n)
