#!/usr/bin/env bash
set -euo pipefail

echo "========================================"
echo " task_system setup"
echo " SQLite is provided by Python's standard library."
echo "========================================"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 not found. Install Python 3.10+ and retry."
  exit 1
fi

echo
echo "[1/3] Installing Python dependencies..."
python3 -m pip install -r task_system/requirements.txt

echo
echo "[2/3] Creating data directory..."
mkdir -p task_system/data/task_embeddings

echo
echo "[3/3] Running schema migration..."
python3 -c "import sys; sys.path.insert(0,'.'); from task_system.index import ensure_schema; ensure_schema(); print('  schema OK')"

echo
echo "========================================"
echo " Setup complete."
echo " task_system/data/tasks.db created."
echo " SQLite support comes from Python's built-in sqlite3 module."
echo " Run: python3 -c \"import sys; sys.path.insert(0,'.'); from task_system import TaskStore; print(TaskStore())\""
echo "========================================"
