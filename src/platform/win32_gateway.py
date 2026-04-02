from __future__ import annotations

from PIL import Image, ImageGrab
import win32con
import win32gui

from src.platform.exceptions import WindowCaptureError, WindowFocusError
from src.platform.gateway import WindowGateway
from src.platform.models import Rect


class PyWin32WindowGateway(WindowGateway):
    def enumerate_windows(self) -> tuple[int, ...]:
        handles: list[int] = []

        def collect(handle: int, _extra: object) -> bool:
            handles.append(int(handle))
            return True

        win32gui.EnumWindows(collect, None)
        return tuple(handles)

    def is_window(self, handle: int) -> bool:
        return bool(win32gui.IsWindow(handle))

    def is_window_visible(self, handle: int) -> bool:
        return bool(win32gui.IsWindowVisible(handle))

    def get_foreground_window(self) -> int:
        return int(win32gui.GetForegroundWindow())

    def focus_window(self, handle: int) -> None:
        try:
            if win32gui.IsIconic(handle):
                win32gui.ShowWindow(handle, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(handle)
        except Exception as exc:
            raise WindowFocusError(f"failed to focus window handle={handle}") from exc

    def get_window_text(self, handle: int) -> str:
        return str(win32gui.GetWindowText(handle))

    def get_class_name(self, handle: int) -> str:
        return str(win32gui.GetClassName(handle))

    def get_window_rect(self, handle: int) -> Rect:
        left, top, right, bottom = win32gui.GetWindowRect(handle)
        return Rect(left=left, top=top, right=right, bottom=bottom)

    def get_client_rect(self, handle: int) -> Rect:
        left, top, right, bottom = win32gui.GetClientRect(handle)
        screen_left, screen_top = win32gui.ClientToScreen(handle, (left, top))
        screen_right, screen_bottom = win32gui.ClientToScreen(handle, (right, bottom))
        return Rect(
            left=screen_left,
            top=screen_top,
            right=screen_right,
            bottom=screen_bottom,
        )

    def capture_rect(self, rect: Rect) -> Image.Image:
        try:
            return ImageGrab.grab(bbox=rect.as_bbox(), all_screens=True)
        except Exception as exc:
            raise WindowCaptureError(f"failed to capture rect={rect.as_bbox()}") from exc