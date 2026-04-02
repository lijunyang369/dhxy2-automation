from __future__ import annotations

from typing import Protocol

from src.domain import BattleObservation
from src.platform import WindowSession


class ObservationProvider(Protocol):
    def observe(self, window_session: WindowSession) -> BattleObservation: ...
