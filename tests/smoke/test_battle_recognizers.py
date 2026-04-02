from __future__ import annotations

import unittest
from datetime import datetime, timezone

from PIL import Image

from src.domain import MatchResult
from src.perception import BattleRecognitionSuite, ObservationBuilder, RecognitionSnapshot
from src.platform import FrameCapture, Rect, WindowInfo


class BattleRecognitionSuiteTestCase(unittest.TestCase):
    def test_battle_scene_is_independent_from_prompt_and_skill_bar(self) -> None:
        snapshot = RecognitionSnapshot(
            matches=(
                MatchResult(
                    template_id="battle_action_prompt",
                    confidence=0.97,
                    region_name="battle_prompt",
                ),
                MatchResult(
                    template_id="battle_skill_bar",
                    confidence=0.95,
                    region_name="skill_bar",
                ),
            ),
            named_regions={
                "round_number_region": (0, 0, 80, 40),
                "battle_auto_button": (1290, 700, 1368, 750),
                "battle_prompt": (1170, 245, 1320, 530),
                "skill_bar": (950, 680, 1378, 831),
            },
            region_images={
                "round_number_region": Image.new("RGB", (80, 40), color="black"),
            },
        )

        results = BattleRecognitionSuite().evaluate(snapshot)

        self.assertFalse(results["battle_scene"].detected)
        self.assertTrue(results["battle_action_prompt"].detected)
        self.assertTrue(results["battle_skill_bar"].detected)

    def test_module_reports_missing_region_without_affecting_others(self) -> None:
        snapshot = RecognitionSnapshot(
            matches=(),
            named_regions={"round_number_region": (0, 0, 180, 50)},
            region_images={"round_number_region": Image.new("RGB", (180, 50), color="black")},
        )

        results = BattleRecognitionSuite().evaluate(snapshot)

        self.assertFalse(results["battle_action_prompt"].detected)
        self.assertFalse(results["battle_action_prompt"].details["region_configured"])


class ObservationBuilderModuleWiringTestCase(unittest.TestCase):
    def test_builder_maps_independent_recognizers_back_to_observation_flags(self) -> None:
        builder = ObservationBuilder()
        frame = FrameCapture(image=Image.new("RGB", (200, 120), color="black"))
        window_info = WindowInfo(
            handle=1001,
            title="dhxy2",
            class_name="DhxyWindow",
            window_rect=Rect(0, 0, 1280, 720),
            client_rect=Rect(8, 32, 1272, 712),
            is_visible=True,
            is_foreground=True,
        )

        observation = builder.build(
            frame=frame,
            window_info=window_info,
            matches=(
                MatchResult(
                    template_id="battle_action_prompt",
                    confidence=0.96,
                    region_name="battle_prompt",
                ),
                MatchResult(
                    template_id="battle_skill_bar",
                    confidence=0.94,
                    region_name="skill_bar",
                ),
            ),
            named_regions={
                "round_number_region": Rect(0, 0, 80, 40),
                "battle_auto_button": Rect(1290, 700, 1368, 750),
                "battle_prompt": Rect(1170, 245, 1320, 530),
                "skill_bar": Rect(950, 680, 1378, 831),
            },
            region_images={
                "round_number_region": Image.new("RGB", (80, 40), color="black"),
            },
        )

        self.assertFalse(observation.battle_ui_visible)
        self.assertTrue(observation.action_prompt_visible)
        self.assertTrue(observation.skill_panel_visible)

    def test_round_number_text_reflects_structured_round_number(self) -> None:
        observation = BattleObservation(
            battle_ui_visible=True,
            action_prompt_visible=True,
            skill_panel_visible=True,
            target_select_visible=False,
            settlement_visible=False,
            window_alive=True,
            window_focused=True,
            frame_timestamp=datetime.now(timezone.utc),
            frame_hash="frame-hash",
            confidence_summary=0.95,
            round_indicator_visible=True,
            round_number=2,
            round_digits=("2",),
        )
        self.assertEqual("2", observation.round_number_text)


from src.domain import BattleObservation


if __name__ == "__main__":
    unittest.main()
