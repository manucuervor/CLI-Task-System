# CLI Task System

CLI Task System is a portable, local-first task store for agent workflows and human review loops.
Its main purpose is to give agents a structured source of truth for tasks, revisions, execution reports, and audits.

Under the hood it provides a small local system backed by:

- an append-only JSONL audit log,
- a SQLite task index with revisions,
- semantic search over task history using FAISS and sentence-transformers.

The project is designed to be copied into any repository or published as its own standalone tool.

## What it solves

When multiple agents or operators share work, a single markdown backlog scales badly. This repo keeps each task structured and queryable:

- create tasks with a full execution spec,
- fetch only the next pending task,
- store execution evidence,
- audit outcomes,
- open corrected revisions without losing history,
- search prior work semantically.

In practice, the intended usage is:

- agents use the task store as the operational source of truth,
- instruction files tell agents when to call the CLI,
- humans only use the CLI directly when reviewing, debugging, or performing manual intervention.

## Repository layout

```text
CLI Task System/
  pyproject.toml
  README.md
  LICENSE
  task_system/
    __init__.py
    cli.py
    compaction.py
    config.py
    index.py
    log.py
    search.py
    store.py
    requirements.txt
    setup.bat
    setup.sh
    data/
```

## Requirements

- Python 3.10+
- Enough local disk space for the SQLite database and FAISS index
- `pip` available in the active Python environment

SQLite is not listed in `requirements.txt` because this project uses Python's built-in `sqlite3` module. If Python 3.10+ is installed, SQLite support is already present.

Semantic search uses [`all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) via `sentence-transformers`. The first semantic search, embedding write, or revision search will download that model and therefore requires network access once.

## Installation

### Option 1: bootstrap with the included Windows script

From the repository root:

```powershell
task_system\setup.bat
```

That script will:

- verify Python is available,
- install Python dependencies,
- create `task_system/data/`,
- initialize the SQLite schema.

### Option 2: manual setup

```powershell
pip install -r task_system\requirements.txt
python -c "import sys; sys.path.insert(0,'.'); from task_system.index import ensure_schema; ensure_schema(); print('schema OK')"
```

### Option 3: bootstrap with the included macOS/Linux script

From the repository root:

```bash
chmod +x task_system/setup.sh
./task_system/setup.sh
```

## Agent integration

If you use instruction files such as `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md`, the recommended approach is to tell agents that the task store is the source of truth and that they should call the CLI when they need to read or update task state.

Example snippet:

```md
## Task system

Use `CLI Task System` as the source of truth for task management.

- Do not create or update task-tracking markdown files manually.
- Create tasks with `python task_system/cli.py create ...`
- Fetch work with `python task_system/cli.py next` or `python task_system/cli.py get TASK-XXX`
- Report execution with `python task_system/cli.py execute TASK-XXX "result"`
- Audit with `python task_system/cli.py audit TASK-XXX done|needs_fix "findings"`
- Create correction revisions with `python task_system/cli.py correct TASK-XXX error_type "fix strategy"`
```

## Recommended workflow

The intended workflow is agent-first:

1. A coordinator, architect, or reviewer creates the task and writes the full spec.
2. The execution agent fetches only the task it needs with `next` or `get`.
3. The execution agent records what happened with `execute`.
4. A reviewer or audit agent closes the task with `audit`.
5. If the result is rejected, a new revision is opened with `correct`.

Humans can still call the CLI directly, but mostly for:

- initial setup,
- manual review,
- debugging,
- inspecting history,
- recovering from unusual situations.

## Quick review commands

If you want to inspect or intervene manually, these are the most useful commands:

- `python task_system/cli.py next`
- `python task_system/cli.py get TASK-001`
- `python task_system/cli.py history TASK-001`
- `python task_system/cli.py search "semantic query"`
- `python task_system/cli.py list`

## Full CLI reference

- `python task_system/cli.py next`
- `python task_system/cli.py get TASK-001`
- `python task_system/cli.py create TASK-001 "summary" "full spec"`
- `python task_system/cli.py execute TASK-001 "result"`
- `python task_system/cli.py audit TASK-001 done "findings"`
- `python task_system/cli.py audit TASK-001 needs_fix "findings"`
- `python task_system/cli.py correct TASK-001 error_type "fix strategy"`
- `python task_system/cli.py history TASK-001`
- `python task_system/cli.py search "semantic query"`
- `python task_system/cli.py list`

## Data location

Runtime data is stored inside `task_system/data/`:

- `tasks.db`
- `task_audit.jsonl`
- `task_embeddings/`

These generated files are ignored by git. The repository keeps only `task_system/data/.gitkeep`.

## Packaging note

The repo now includes `pyproject.toml` so it can evolve into a proper distributable package, but the current primary interface is still the CLI entry script at `task_system/cli.py`.

## License

MIT
