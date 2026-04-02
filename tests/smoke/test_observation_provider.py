from __future__ import annotations

import unittest

from PIL import Image

from src.app import DefaultObservationProvider, DefaultObservationProviderConfig
from src.domain import MatchResult
from src.perception import RegionRequest
from src.platform import FrameCapture, Rect, WindowSession


class FakeWindowGateway:
    def is_window(self, handle: int) -> bool:
        return handle == 1001

    def is_window_visible(self, handle: int) -> bool:
        return True

    def get_foreground_window(self) -> int:
        return 1001

    def focus_window(self, handle: int) -> None:
        pass

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


class FakeTemplateMatcher:
    def match(self, frame: FrameCapture, region_name: str, rect: Rect | None = None) -> tuple[MatchResult, ...]:
        payload = {
            "battle_auto_button": (MatchResult(template_id="battle_ui", confidence=0.96, region_name=region_name),),
            "battle_prompt": (MatchResult(template_id="battle_action_prompt", confidence=0.94, region_name=region_name),),
            "skill_bar": (MatchResult(template_id="battle_skill_bar", confidence=0.92, region_name=region_name),),
        }
        return payload.get(region_name, ())


class DefaultObservationProviderTestCase(unittest.TestCase):
    def test_observe_collects_window_frame_matches(self) -> None:
        provider = DefaultObservationProvider(
            template_matcher=FakeTemplateMatcher(),
            config=DefaultObservationProviderConfig(
                regions=(
                    RegionRequest(name="battle_main", rect=Rect(0, 0, 100, 100), use_template_match=True),
                    RegionRequest(name="battle_auto_button", rect=Rect(80, 80, 160, 120), use_template_match=True),
                    RegionRequest(name="battle_prompt", rect=Rect(10, 10, 110, 50), use_template_match=True),
                    RegionRequest(name="skill_bar", rect=Rect(20, 60, 140, 100), use_template_match=True),
                )
            ),
        )
        session = WindowSession(handle=1001, gateway=FakeWindowGateway())

        observation = provider.observe(session)

        self.assertTrue(observation.battle_ui_visible)
        self.assertTrue(observation.action_prompt_visible)
        self.assertTrue(observation.skill_panel_visible)
        self.assertEqual(3, len(observation.matches))
        self.assertIn("battle_prompt", observation.named_regions)


if __name__ == "__main__":
    unittest.main()
