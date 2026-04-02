from __future__ import annotations

import unittest

from PIL import Image

from src.perception import build_battle_command_calibration_suggestion, detect_battle_command_buttons
from tests.smoke._paths import RESOURCES_ROOT, RUNS_ROOT


class BattleCommandButtonDetectionTestCase(unittest.TestCase):
    def test_detects_full_battle_command_menu_from_library_template(self) -> None:
        frame = Image.open(RUNS_ROOT / "artifacts" / "probes" / "battle-item-confirm-before.png")
        menu_template = Image.open(RESOURCES_ROOT / "templates" / "battle" / "battle_action_menu.png")

        detections = detect_battle_command_buttons(
            frame,
            ["spell", "item", "defend", "protect", "summon", "recall", "catch", "escape"],
            action_menu_template=menu_template,
        )

        self.assertEqual(8, len(detections))
        self.assertEqual("spell", detections[0].name)
        self.assertEqual("escape", detections[-1].name)
        self.assertTrue(all(detections[index].center[1] < detections[index + 1].center[1] for index in range(7)))
        self.assertTrue(all(detection.center[0] >= 1240 for detection in detections))

    def test_builds_calibration_suggestion_from_detections(self) -> None:
        frame = Image.open(RUNS_ROOT / "artifacts" / "probes" / "battle-item-confirm-before.png")
        menu_template = Image.open(RESOURCES_ROOT / "templates" / "battle" / "battle_action_menu.png")
        detections = detect_battle_command_buttons(
            frame,
            ["spell", "item", "defend", "protect", "summon", "recall", "catch", "escape"],
            action_menu_template=menu_template,
        )

        suggestion = build_battle_command_calibration_suggestion(
            detections,
            labels_by_name={"spell": "娉曟湳", "defend": "闃插尽", "escape": "閫冭窇"},
        )

        self.assertEqual(1247, suggestion.layout["x"])
        self.assertEqual(267, suggestion.layout["start_y"])
        self.assertEqual(34, suggestion.layout["step_y"])
        self.assertEqual([1247, 267], suggestion.buttons["spell"]["point"])
        self.assertEqual("娉曟湳", suggestion.buttons["spell"]["label"])
        self.assertEqual("candidate", suggestion.buttons["escape"]["status"])


if __name__ == "__main__":
    unittest.main()
