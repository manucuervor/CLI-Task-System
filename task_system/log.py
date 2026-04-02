import json
from datetime import datetime, timezone
from . import config

def append_event(task_id: str, revision: int, actor: str, action: str, payload: dict = None) -> None:
    config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "task_id":   task_id,
        "revision":  revision,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor":     actor,
        "action":    action,
        "payload":   payload or {}
    }
    with open(config.LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
