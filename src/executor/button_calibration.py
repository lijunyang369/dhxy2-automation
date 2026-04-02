from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ButtonPoint:
    group: str
    name: str
    x: int
    y: int
    status: str
    label: str | None = None

    @property
    def point(self) -> tuple[int, int]:
        return (self.x, self.y)


class ButtonCalibration:
    def __init__(self, buttons: dict[str, ButtonPoint]) -> None:
        self._buttons = buttons

    @classmethod
    def load(cls, path: Path) -> "ButtonCalibration":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        buttons: dict[str, ButtonPoint] = {}
        for group_name, group_payload in payload.items():
            if group_name == "version":
                continue
            group_buttons = group_payload.get("buttons", {})
            for button_name, button_payload in group_buttons.items():
                point = button_payload["point"]
                ref = f"{group_name}.{button_name}"
                buttons[ref] = ButtonPoint(
                    group=group_name,
                    name=button_name,
                    x=int(point[0]),
                    y=int(point[1]),
                    status=str(button_payload.get("status", "unknown")),
                    label=button_payload.get("label"),
                )
        return cls(buttons)

    def resolve(self, button_ref: str) -> tuple[int, int]:
        button = self._buttons.get(button_ref)
        if button is None:
            raise KeyError(f"unknown button_ref={button_ref}")
        return button.point

    def get(self, button_ref: str) -> ButtonPoint | None:
        return self._buttons.get(button_ref)

    def has(self, button_ref: str) -> bool:
        return button_ref in self._buttons
