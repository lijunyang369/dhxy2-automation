from __future__ import annotations

import unittest

from PIL import Image

from src.domain import MatchResult
from src.perception import ObservationBuilder, RegionCropper, RegionSpec
from src.platform import FrameCapture, Rect, WindowInfo


class ObservationBuilderTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = FrameCapture(image=Image.new("RGB", (200, 100), color="black"))
        self.window_info = WindowInfo(
            handle=1001,
            title="dhxy2",
            class_name="DhxyWindow",
            window_rect=Rect(0, 0, 1280, 720),
            client_rect=Rect(8, 32, 1272, 712),
            is_visible=True,
            is_foreground=True,
        )
        self.builder = ObservationBuilder()

    def test_build_sets_battle_flags_from_template_ids(self) -> None:
        matches = (
            MatchResult(template_id="battle_ui", confidence=0.96, region_name="battle_auto_button"),
            MatchResult(template_id="battle_action_prompt", confidence=0.93, region_name="battle_prompt"),
            MatchResult(template_id="battle_skill_bar", confidence=0.91, region_name="skill_bar"),
        )

        observation = self.builder.build(
            frame=self.frame,
            window_info=self.window_info,
            matches=matches,
            named_regions={
                "battle_main": Rect(0, 0, 100, 40),
                "battle_auto_button": Rect(120, 70, 180, 110),
                "battle_prompt": Rect(10, 10, 100, 40),
                "skill_bar": Rect(20, 60, 140, 100),
            },
        )

        self.assertTrue(observation.battle_ui_visible)
        self.assertTrue(observation.action_prompt_visible)
        self.assertTrue(observation.skill_panel_visible)
        self.assertFalse(observation.settlement_visible)
        self.assertEqual(self.frame.frame_hash, observation.frame_hash)
        self.assertAlmostEqual(0.9333, observation.confidence_summary, places=2)

    def test_region_cropper_returns_expected_region_size(self) -> None:
        cropper = RegionCropper()
        region = RegionSpec(name="battle_prompt", rect=Rect(20, 10, 80, 40))

        cropped = cropper.crop(self.frame, region)

        self.assertEqual((60, 30), cropped.size)

    def test_build_supports_settlement_signal(self) -> None:
        matches = (
            MatchResult(template_id="battle_settlement", confidence=0.97, region_name="settlement_panel"),
        )

        observation = self.builder.build(
            frame=self.frame,
            window_info=self.window_info,
            matches=matches,
            named_regions={"settlement_panel": Rect(20, 10, 120, 60)},
        )

        self.assertTrue(observation.settlement_visible)
        self.assertFalse(observation.action_prompt_visible)


if __name__ == "__main__":
    unittest.main()
