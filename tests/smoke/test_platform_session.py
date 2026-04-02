from __future__ import annotations

import unittest

from PIL import Image

from src.platform import Rect, WindowNotFoundError, WindowSession


class FakeWindowGateway:
    def __init__(self) -> None:
        self.valid = True
        self.focused = False

    def is_window(self, handle: int) -> bool:
        return self.valid and handle == 1001

    def is_window_visible(self, handle: int) -> bool:
        return True

    def get_foreground_window(self) -> int:
        return 1001 if self.focused else 0

    def focus_window(self, handle: int) -> None:
        self.focused = True

    def get_window_text(self, handle: int) -> str:
        return "dhxy2"

    def get_class_name(self, handle: int) -> str:
        return "DhxyWindow"

    def get_window_rect(self, handle: int) -> Rect:
        return Rect(0, 0, 1280, 720)

    def get_client_rect(self, handle: int) -> Rect:
        return Rect(8, 32, 1272, 712)

    def capture_rect(self, rect: Rect) -> Image.Image:
        return Image.new("RGB", (rect.width, rect.height), color="black")


class WindowSessionTestCase(unittest.TestCase):
    def test_snapshot_reads_window_metadata(self) -> None:
        session = WindowSession(handle=1001, gateway=FakeWindowGateway())

        info = session.snapshot()

        self.assertEqual("dhxy2", info.title)
        self.assertEqual("DhxyWindow", info.class_name)
        self.assertEqual(1264, info.client_rect.width)
        self.assertFalse(info.is_foreground)

    def test_focus_updates_foreground_state(self) -> None:
        gateway = FakeWindowGateway()
        session = WindowSession(handle=1001, gateway=gateway)

        session.focus()
        info = session.snapshot()

        self.assertTrue(info.is_foreground)

    def test_capture_client_returns_frame_capture(self) -> None:
        session = WindowSession(handle=1001, gateway=FakeWindowGateway())

        frame = session.capture_client()

        self.assertEqual("client", frame.source)
        self.assertEqual("dhxy2", frame.metadata["title"])
        self.assertTrue(frame.frame_hash)

    def test_missing_window_raises(self) -> None:
        gateway = FakeWindowGateway()
        gateway.valid = False
        session = WindowSession(handle=1001, gateway=gateway)

        with self.assertRaises(WindowNotFoundError):
            session.snapshot()


if __name__ == "__main__":
    unittest.main()
