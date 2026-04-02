from __future__ import annotations

from typing import Protocol

from src.domain import MatchResult
from src.platform import FrameCapture
from src.platform.models import Rect


class TemplateMatcher(Protocol):
    def match(self, frame: FrameCapture, region_name: str, rect: Rect | None = None) -> tuple[MatchResult, ...]: ...
