"""
Command-line interface for the Task Store.

Usage (run from the repository root):

  python task_system/cli.py next
  python task_system/cli.py get TASK-001
  python task_system/cli.py execute TASK-001 "implementation result"
  python task_system/cli.py create TASK-002 "summary" "full spec"
  python task_system/cli.py audit TASK-001 done "findings"
  python task_system/cli.py audit TASK-001 needs_fix "findings"
  python task_system/cli.py correct TASK-001 validation_error "fix strategy"
  python task_system/cli.py history TASK-001
  python task_system/cli.py search "semantic query"
  python task_system/cli.py list
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from task_system import TaskStore

store = TaskStore()


def cmd_next():
    task = store.get_next_pending()
    if task is None:
        print("No pending tasks.")
        return
    _print_task(task)


def cmd_get(task_id):
    task = store.get_task_with_spec(task_id)
    if task is None:
        print(f"Task not found: {task_id}")
        sys.exit(1)
    _print_task(task)


def cmd_execute(task_id, result):
    store.execute_task(task_id, result, actor="executor")
    print(f"[execute] {task_id} recorded.")


def cmd_create(task_id, summary, spec):
    store.create_task(task_id, summary, spec, actor="architect")
    print(f"[create] {task_id} created and pending.")


def cmd_audit(task_id, status, findings):
    if status not in ("done", "needs_fix"):
        print(f"Error: status must be 'done' or 'needs_fix', got '{status}'")
        sys.exit(1)
    store.audit_task(task_id, findings, status, actor="architect")
    verdict = "APPROVED" if status == "done" else "REJECTED (needs_fix)"
    print(f"[audit] {task_id} - {verdict}")


def cmd_correct(task_id, error_type, fix_strategy, spec=None):
    store.correct_task(task_id, fix_strategy, error_type, spec=spec, actor="architect")
    task = store.get_task(task_id)
    print(f"[correct] {task_id} - revision {task['current_revision']} created.")


def cmd_history(task_id):
    revisions = store.get_history(task_id)
    if not revisions:
        print(f"No history for {task_id}")
        return
    print(f"\n{'=' * 60}")
    print(f"History for {task_id} ({len(revisions)} revisions)")
    print(f"{'=' * 60}")
    for rev in revisions:
        parent = f"<- rev{rev['parent_revision']}" if rev['parent_revision'] else "(initial)"
        print(f"\n  Rev {rev['revision']} {parent} | {rev['status']} | actor: {rev['actor']}")
        print(f"  Summary: {rev['summary']}")
        if rev.get('error_type'):
            print(f"  Error:   {rev['error_type']}")
        if rev.get('fix_strategy'):
            print(f"  Fix:     {rev['fix_strategy']}")


def cmd_search(query):
    results = store.search(query, top_k=5)
    if not results:
        print("No results.")
        return
    print(f"\nResults for: \"{query}\"\n")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['task_id']} rev{result['revision']} [{result['status']}] score={result['score']:.4f}")
        print(f"     {result['summary']}")


def cmd_list():
    import sqlite3
    from task_system import config

    con = sqlite3.connect(str(config.DB_PATH))
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT task_id, current_revision, status, created_at "
        "FROM agent_tasks ORDER BY created_at DESC"
    ).fetchall()
    con.close()
    if not rows:
        print("No tasks in the system.")
        return
    print(f"\n{'TASK_ID':<14} {'REV':<5} {'STATUS':<12} {'CREATED'}")
    print("-" * 60)
    for row in rows:
        print(f"{row['task_id']:<14} {row['current_revision']:<5} {row['status']:<12} {row['created_at'][:19]}")


def _print_task(task):
    print(f"\n{'=' * 60}")
    print(f"  {task['task_id']} | {task['status']} | rev {task['current_revision']}")
    print(f"{'=' * 60}")
    print(f"  Summary: {task['summary']}")
    print("\n--- SPEC ---\n")
    print(task.get('spec') or '(no spec)')
    print(f"\n{'=' * 60}\n")


def usage():
    print(__doc__)
    sys.exit(1)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        usage()

    cmd = args[0]

    if cmd == "next":
        cmd_next()
    elif cmd == "get" and len(args) == 2:
        cmd_get(args[1])
    elif cmd == "execute" and len(args) == 3:
        cmd_execute(args[1], args[2])
    elif cmd == "create" and len(args) == 4:
        cmd_create(args[1], args[2], args[3])
    elif cmd == "audit" and len(args) == 4:
        cmd_audit(args[1], args[2], args[3])
    elif cmd == "correct" and len(args) >= 4:
        spec = args[4] if len(args) == 5 else None
        cmd_correct(args[1], args[2], args[3], spec)
    elif cmd == "history" and len(args) == 2:
        cmd_history(args[1])
    elif cmd == "search" and len(args) == 2:
        cmd_search(args[1])
    elif cmd == "list":
        cmd_list()
    else:
        usage()
