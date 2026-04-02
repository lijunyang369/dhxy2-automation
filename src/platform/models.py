from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
from typing import Any

from PIL import Image


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    def as_bbox(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)


@dataclass(frozen=True)
class WindowInfo:
    handle: int
    title: str
    class_name: str
    window_rect: Rect
    client_rect: Rect
    is_visible: bool
    is_foreground: bool


@dataclass(frozen=True)
class FrameCapture:
    image: Image.Image
    captured_at: datetime = field(default_factory=utc_now)
    source: str = "client"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def frame_hash(self) -> str:
        return hashlib.md5(self.image.tobytes()).hexdigest()
