from __future__ import annotations

from dataclasses import dataclass

from src.platform.exceptions import WindowNotFoundError
from src.platform.gateway import WindowGateway
from src.platform.models import FrameCapture, WindowInfo


@dataclass
class WindowSession:
    handle: int
    gateway: WindowGateway

    def exists(self) -> bool:
        return self.gateway.is_window(self.handle)

    def ensure_alive(self) -> None:
        if not self.exists():
            raise WindowNotFoundError(f"window handle={self.handle} is not available")

    def focus(self) -> None:
        self.ensure_alive()
        self.gateway.focus_window(self.handle)

    def snapshot(self) -> WindowInfo:
        self.ensure_alive()
        return WindowInfo(
            handle=self.handle,
            title=self.gateway.get_window_text(self.handle),
            class_name=self.gateway.get_class_name(self.handle),
            window_rect=self.gateway.get_window_rect(self.handle),
            client_rect=self.gateway.get_client_rect(self.handle),
            is_visible=self.gateway.is_window_visible(self.handle),
            is_foreground=self.gateway.get_foreground_window() == self.handle,
        )

    def capture_client(self) -> FrameCapture:
        info = self.snapshot()
        image = self.gateway.capture_rect(info.client_rect)
        return FrameCapture(
            image=image,
            source="client",
            metadata={
                "handle": self.handle,
                "title": info.title,
                "class_name": info.class_name,
            },
        )
