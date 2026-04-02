from __future__ import annotations

import argparse
import ctypes
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image
import win32gui
import win32ui

from src.app.bootstrap import JsonConfigLoader
from src.platform import PyWin32WindowGateway, WindowFinder, WindowSearchCriteria
from src.platform.models import FrameCapture

ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)
INPUT_MOUSE = 0
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
SM_CXSCREEN = 0
SM_CYSCREEN = 1
SRCCOPY = 0x00CC0020


class MOUSEINPUT(ctypes.Structure):
    _fields_ = (
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ULONG_PTR),
    )


class _INPUT_UNION(ctypes.Union):
    _fields_ = (("mi", MOUSEINPUT),)


class INPUT(ctypes.Structure):
    _anonymous_ = ("union",)
    _fields_ = (("type", ctypes.c_ulong), ("union", _INPUT_UNION))


@dataclass(frozen=True)
class ProbeResult:
    label: str
    handle: int
    screen_x: int
    screen_y: int
    client_x: int
    client_y: int
    before_path: str
    after_path: str
    before_hash: str
    after_hash: str
    frame_changed: bool
    send_count: int
    last_error: int


def _send_mouse_click(screen_x: int, screen_y: int) -> tuple[int, int]:
    screen_width = ctypes.windll.user32.GetSystemMetrics(SM_CXSCREEN) - 1
    screen_height = ctypes.windll.user32.GetSystemMetrics(SM_CYSCREEN) - 1
    absolute_x = round(screen_x * 65535 / max(screen_width, 1))
    absolute_y = round(screen_y * 65535 / max(screen_height, 1))
    events = (
        INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(dx=absolute_x, dy=absolute_y, mouseData=0, dwFlags=MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=None)),
        INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(dx=absolute_x, dy=absolute_y, mouseData=0, dwFlags=MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=None)),
        INPUT(type=INPUT_MOUSE, mi=MOUSEINPUT(dx=absolute_x, dy=absolute_y, mouseData=0, dwFlags=MOUSEEVENTF_LEFTUP | MOUSEEVENTF_ABSOLUTE, time=0, dwExtraInfo=None)),
    )
    array_type = INPUT * len(events)
    sent = ctypes.windll.user32.SendInput(len(events), array_type(*events), ctypes.sizeof(INPUT))
    return int(sent), int(ctypes.GetLastError())


def _capture_window_bitblt(handle: int) -> FrameCapture:
    left, top, right, bottom = win32gui.GetWindowRect(handle)
    width = max(0, right - left)
    height = max(0, bottom - top)
    hwnd_dc = win32gui.GetWindowDC(handle)
    src_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    mem_dc = src_dc.CreateCompatibleDC()
    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(src_dc, width, height)
    mem_dc.SelectObject(bitmap)
    try:
        mem_dc.BitBlt((0, 0), (width, height), src_dc, (0, 0), SRCCOPY)
        bmpinfo = bitmap.GetInfo()
        bmpbytes = bitmap.GetBitmapBits(True)
        image = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpbytes, "raw", "BGRX", 0, 1)
        return FrameCapture(image=image.copy(), source="bitblt", metadata={"handle": handle})
    finally:
        win32gui.DeleteObject(bitmap.GetHandle())
        mem_dc.DeleteDC()
        src_dc.DeleteDC()
        win32gui.ReleaseDC(handle, hwnd_dc)


def _resolve_session(project_root: Path):
    loader = JsonConfigLoader()
    account_config = loader.load(project_root / "configs" / "accounts" / "instance-1.json")
    gateway = PyWin32WindowGateway()
    finder = WindowFinder(gateway)
    return finder.find(WindowSearchCriteria(
        title_contains=account_config.get("window_title"),
        class_name=account_config.get("window_class"),
        handle=account_config.get("window_handle"),
        require_visible=True,
    ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--center-x", type=int, required=True)
    parser.add_argument("--center-y", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--offsets", required=True, help="comma-separated x:y pairs")
    parser.add_argument("--delay", type=float, default=0.8)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    output_root = project_root / "runs" / "artifacts" / "probes" / args.label
    output_root.mkdir(parents=True, exist_ok=True)

    session = _resolve_session(project_root)
    session.focus()
    time.sleep(0.25)
    info = session.snapshot()

    results = []
    for raw in [item.strip() for item in args.offsets.split(",") if item.strip()]:
        dx_str, dy_str = raw.split(":", 1)
        client_x = args.center_x + int(dx_str)
        client_y = args.center_y + int(dy_str)
        label = f"{args.label}_{dx_str}_{dy_str}".replace("-", "m")
        before = _capture_window_bitblt(info.handle)
        before_path = output_root / f"{label}-before.png"
        before.image.save(before_path)
        screen_x = info.client_rect.left + client_x
        screen_y = info.client_rect.top + client_y
        send_count, last_error = _send_mouse_click(screen_x, screen_y)
        time.sleep(args.delay)
        after = _capture_window_bitblt(info.handle)
        after_path = output_root / f"{label}-after.png"
        after.image.save(after_path)
        result = ProbeResult(
            label=label,
            handle=info.handle,
            screen_x=screen_x,
            screen_y=screen_y,
            client_x=client_x,
            client_y=client_y,
            before_path=str(before_path),
            after_path=str(after_path),
            before_hash=before.frame_hash,
            after_hash=after.frame_hash,
            frame_changed=before.frame_hash != after.frame_hash,
            send_count=send_count,
            last_error=last_error,
        )
        results.append(asdict(result))
        time.sleep(0.25)

    summary_path = output_root / "summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

