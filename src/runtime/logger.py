from __future__ import annotations

import json
from pathlib import Path

from src.runtime.events import RuntimeEvent


class RuntimeLogger:
    def __init__(self, log_dir: Path) -> None:
        self._runtime_log = log_dir / "runtime.log"

    def log(self, event: RuntimeEvent) -> Path:
        payload = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "instance_id": event.instance_id,
            "battle_session_id": event.battle_session_id,
            "state": event.state,
            "message": event.message,
            "details": event.details,
        }
        with self._runtime_log.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return self._runtime_log
