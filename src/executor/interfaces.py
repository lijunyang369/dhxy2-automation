from __future__ import annotations

from typing import Protocol


class InputGateway(Protocol):
    def click(self, x: int, y: int) -> None: ...

    def press_key(self, key: str) -> None: ...

    def wait(self, seconds: float) -> None: ...
