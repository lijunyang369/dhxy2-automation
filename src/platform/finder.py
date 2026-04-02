from __future__ import annotations

from dataclasses import dataclass

from src.platform.exceptions import WindowNotFoundError
from src.platform.gateway import WindowGateway
from src.platform.models import Rect, WindowInfo
from src.platform.session import WindowSession


@dataclass(frozen=True)
class WindowSearchCriteria:
    title_contains: str | None = None
    class_name: str | None = None
    handle: int | None = None
    require_visible: bool = True


class WindowFinder:
    def __init__(self, gateway: WindowGateway) -> None:
        self._gateway = gateway

    def find(self, criteria: WindowSearchCriteria) -> WindowSession:
        if criteria.handle is not None and self._gateway.is_window(criteria.handle):
            if self._matches(criteria.handle, criteria):
                return WindowSession(handle=criteria.handle, gateway=self._gateway)

        for handle in self._gateway.enumerate_windows():
            if not self._gateway.is_window(handle):
                continue
            if criteria.require_visible and not self._gateway.is_window_visible(handle):
                continue
            if not self._matches(handle, criteria):
                continue
            return WindowSession(handle=handle, gateway=self._gateway)

        raise WindowNotFoundError(
            f"no window matched title_contains={criteria.title_contains!r}, class_name={criteria.class_name!r}, handle={criteria.handle!r}"
        )

    def _matches(self, handle: int, criteria: WindowSearchCriteria) -> bool:
        title = self._gateway.get_window_text(handle)
        class_name = self._gateway.get_class_name(handle)
        if criteria.title_contains and criteria.title_contains.lower() not in title.lower():
            return False
        if criteria.class_name and criteria.class_name != class_name:
            return False
        return True
