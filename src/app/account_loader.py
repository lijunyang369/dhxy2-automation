from __future__ import annotations

import json
from pathlib import Path

from src.domain import AccountBinding, WindowBinding


class AccountBindingLoader:
    def load(self, path: Path) -> AccountBinding:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        return AccountBinding(
            instance_id=str(payload["instance_id"]),
            enabled=bool(payload.get("enabled", True)),
            character_config_ref=_optional_string(payload.get("character_config")),
            window=WindowBinding(
                handle=_optional_int(payload.get("window_handle")),
                title=_optional_string(payload.get("window_title")),
                class_name=_optional_string(payload.get("window_class")),
            ),
        )


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)
