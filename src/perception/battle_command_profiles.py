from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BattleCommandProfile:
    profile_key: str
    label: str
    group: str
    menu_button_names: tuple[str, ...]
    labels_by_name: dict[str, str]
    seed_button_refs: tuple[str, ...] = ()
    notes: str | None = None


class BattleCommandProfileCatalog:
    def __init__(self, profiles: dict[str, BattleCommandProfile]) -> None:
        self._profiles = profiles

    @classmethod
    def load(cls, path: Path) -> "BattleCommandProfileCatalog":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        profiles: dict[str, BattleCommandProfile] = {}
        for profile_key, profile_payload in payload.get("profiles", {}).items():
            profiles[profile_key] = BattleCommandProfile(
                profile_key=profile_key,
                label=str(profile_payload["label"]),
                group=str(profile_payload["group"]),
                menu_button_names=tuple(str(item) for item in profile_payload.get("menu_button_names", ())),
                labels_by_name={str(key): str(value) for key, value in profile_payload.get("labels_by_name", {}).items()},
                seed_button_refs=tuple(str(item) for item in profile_payload.get("seed_button_refs", ())),
                notes=profile_payload.get("notes"),
            )
        return cls(profiles)

    def get(self, profile_key: str) -> BattleCommandProfile | None:
        return self._profiles.get(profile_key)

