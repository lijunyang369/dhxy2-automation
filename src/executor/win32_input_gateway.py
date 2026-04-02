from __future__ import annotations

import ctypes
import time

import win32gui


ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

KEYEVENTF_KEYUP = 0x0002

SM_CXSCREEN = 0
SM_CYSCREEN = 1

_VK_MAP = {
    "ENTER": 0x0D,
    "ESC": 0x1B,
    "TAB": 0x09,
    "SPACE": 0x20,
    "UP": 0x26,
    "DOWN": 0x28,
    "LEFT": 0x25,
    "RIGHT": 0x27,
}


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    )


class KEYBDINPUT(ctypes.Structure):
    _fields_ = (
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    )


class _INPUT_UNION(ctypes.Union):
    _fields_ = (
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
    )


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = (
        ("type", ctypes.c_ulong),
        ("union", _INPUT_UNION),
    )


class Win32SendInputGateway:
    def __init__(self) -> None:
        self.operations: list[tuple[str, object]] = []

    def click(self, x: int, y: int) -> None:
        screen_x, screen_y = _client_to_screen(x, y)
        self._click_screen(screen_x, screen_y)
        self.operations.append(("click", (x, y)))

    def click_screen(self, screen_x: int, screen_y: int) -> None:
        self._click_screen(screen_x, screen_y)
        self.operations.append(("click_screen", (int(screen_x), int(screen_y))))

    def _click_screen(self, screen_x: int, screen_y: int) -> None:
        absolute_x, absolute_y = _to_absolute(screen_x, screen_y)
        events = (
            INPUT(
                type=INPUT_MOUSE,
                mi=MOUSEINPUT(
                    dx=absolute_x,
                    dy=absolute_y,
                    mouseData=0,
                    dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE,
                    time=0,
                    dwExtraInfo=None,
                ),
            ),
            INPUT(
                type=INPUT_MOUSE,
                mi=MOUSEINPUT(
                    dx=absolute_x,
                    dy=absolute_y,
                    mouseData=0,
                    dwFlags=MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE,
                    time=0,
                    dwExtraInfo=None,
                ),
            ),
            INPUT(
                type=INPUT_MOUSE,
                mi=MOUSEINPUT(
                    dx=absolute_x,
                    dy=absolute_y,
                    mouseData=0,
                    dwFlags=MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE,
                    time=0,
                    dwExtraInfo=None,
                ),
            ),
        )
        _send_inputs(events)

    def press_key(self, key: str) -> None:
        vk = _to_vk(key)
        events = (
            INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=0, time=0, dwExtraInfo=None),
            ),
            INPUT(
                type=INPUT_KEYBOARD,
                ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=KEYEVENTF_KEYUP, time=0, dwExtraInfo=None),
            ),
        )
        _send_inputs(events)
        self.operations.append(("key", key))

    def wait(self, seconds: float) -> None:
        time.sleep(max(0.0, float(seconds)))
        self.operations.append(("wait", float(seconds)))


def _send_inputs(events: tuple[INPUT, ...]) -> None:
    array_type = INPUT * len(events)
    sent = ctypes.windll.user32.SendInput(len(events), array_type(*events), ctypes.sizeof(INPUT))
    if int(sent) != len(events):
        raise RuntimeError(f"SendInput failed: sent={sent} expected={len(events)}")


def _to_absolute(screen_x: int, screen_y: int) -> tuple[int, int]:
    screen_width = ctypes.windll.user32.GetSystemMetrics(SM_CXSCREEN) - 1
    screen_height = ctypes.windll.user32.GetSystemMetrics(SM_CYSCREEN) - 1
    absolute_x = round(int(screen_x) * 65535 / max(screen_width, 1))
    absolute_y = round(int(screen_y) * 65535 / max(screen_height, 1))
    return absolute_x, absolute_y


def _client_to_screen(client_x: int, client_y: int) -> tuple[int, int]:
    handle = int(win32gui.GetForegroundWindow())
    if handle <= 0:
        raise RuntimeError("no foreground window available for client-to-screen conversion")
    screen_x, screen_y = win32gui.ClientToScreen(handle, (int(client_x), int(client_y)))
    return int(screen_x), int(screen_y)


def _to_vk(raw_key: str) -> int:
    key = str(raw_key).strip()
    if not key:
        raise ValueError("key must not be empty")

    upper = key.upper()
    if upper in _VK_MAP:
        return int(_VK_MAP[upper])

    if len(upper) == 1 and ("A" <= upper <= "Z" or "0" <= upper <= "9"):
        return ord(upper)

    raise ValueError(f"unsupported key={raw_key}")
