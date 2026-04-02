from pathlib import Path

_HERE = Path(__file__).parent
DATA_DIR = _HERE / "data"

# Estas rutas se resuelven relativas a la carpeta task_system/
# No editar salvo que quieras almacenar los datos en otra ubicación.
DB_PATH   = DATA_DIR / "tasks.db"
LOG_PATH  = DATA_DIR / "task_audit.jsonl"
INDEX_DIR = DATA_DIR / "task_embeddings"
