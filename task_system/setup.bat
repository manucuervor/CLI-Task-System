@echo off
setlocal

echo ========================================
echo  task_system setup
echo ========================================
echo  SQLite is provided by Python's standard library.
echo ========================================

:: 1. Verify Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ and retry.
    exit /b 1
)

:: 2. Install dependencies
echo.
echo [1/3] Installing Python dependencies...
python -m pip install -r task_system\requirements.txt
if errorlevel 1 (
    echo [ERROR] pip install failed.
    exit /b 1
)

:: 3. Create data directory
echo.
echo [2/3] Creating data directory...
if not exist task_system\data mkdir task_system\data
if not exist task_system\data\task_embeddings mkdir task_system\data\task_embeddings

:: 4. Run schema migration
echo.
echo [3/3] Running schema migration...
python -c "import sys; sys.path.insert(0,'.'); from task_system.index import ensure_schema; ensure_schema(); print('  schema OK')"
if errorlevel 1 (
    echo [ERROR] Schema migration failed.
    exit /b 1
)

echo.
echo ========================================
echo  Setup complete.
echo  task_system/data/tasks.db created.
echo  SQLite support comes from Python's built-in sqlite3 module.
echo  Run: python -c "from task_system import TaskStore; print(TaskStore())"
echo ========================================
endlocal
