from __future__ import annotations

import json
import unittest

from src.domain import ActionType, AutomationAction
from src.executor import ActionExecutor, ActionTranslationError, ActionTranslator, ButtonCalibration
from src.platform import Rect, WindowSession
from tests.smoke._paths import CONFIGS_ROOT


class FakeWindowGateway:
    def __init__(self) -> None:
        self.focused = False

    def is_window(self, handle: int) -> bool:
        return handle == 1001

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

    def capture_rect(self, rect: Rect):
        raise NotImplementedError


class FakeInputGateway:
    def __init__(self) -> None:
        self.operations: list[tuple[str, object]] = []

    def click(self, x: int, y: int) -> None:
        self.operations.append(("click", (x, y)))

    def press_key(self, key: str) -> None:
        self.operations.append(("key", key))

    def wait(self, seconds: float) -> None:
        self.operations.append(("wait", seconds))


class ButtonCalibrationTestCase(unittest.TestCase):
    def test_load_and_resolve_button_point(self) -> None:
        calibration_path = CONFIGS_ROOT / "ui" / "button-calibration.json"
        calibration = ButtonCalibration.load(calibration_path)
        payload = json.loads(calibration_path.read_text(encoding="utf-8-sig"))

        self.assertTrue(calibration.has("nonbattle_toolbar.pet_panel"))
        self.assertEqual((910, 802), calibration.resolve("nonbattle_toolbar.pet_panel"))
        self.assertEqual(802, payload["nonbattle_toolbar"]["baseline_y"])
        self.assertEqual(802, payload["nonbattle_toolbar"]["layout"]["y"])


class ActionExecutorTestCase(unittest.TestCase):
    def setUp(self) -> None:
        calibration = ButtonCalibration.load(CONFIGS_ROOT / "ui" / "button-calibration.json")
        self.executor = ActionExecutor(translator=ActionTranslator(button_calibration=calibration))
        self.window_session = WindowSession(handle=1001, gateway=FakeWindowGateway())
        self.input_gateway = FakeInputGateway()

    def test_cast_skill_executes_click_sequence(self) -> None:
        action = AutomationAction(
            action_type=ActionType.CAST_SKILL,
            parameters={
                "skill_point": (100, 200),
                "target_point": (300, 400),
                "confirm_point": (500, 600),
            },
        )

        result = self.executor.execute(action, self.window_session, self.input_gateway)

        self.assertTrue(result.success)
        self.assertEqual(
            [("click", (100, 200)), ("click", (300, 400)), ("click", (500, 600))],
            self.input_gateway.operations,
        )

    def test_click_ui_button_executes_calibrated_point(self) -> None:
        action = AutomationAction(
            action_type=ActionType.CLICK_UI_BUTTON,
            parameters={"button_ref": "nonbattle_toolbar.bag_panel"},
        )

        result = self.executor.execute(action, self.window_session, self.input_gateway)

        self.assertTrue(result.success)
        self.assertEqual([("click", (950, 802))], self.input_gateway.operations)

    def test_click_ui_button_executes_character_battle_command_point(self) -> None:
        action = AutomationAction(
            action_type=ActionType.CLICK_UI_BUTTON,
            parameters={"button_ref": "battle_command_bar.defend"},
        )

        result = self.executor.execute(action, self.window_session, self.input_gateway)

        self.assertTrue(result.success)
        self.assertEqual([("click", (1300, 355))], self.input_gateway.operations)

    def test_click_ui_button_executes_pet_battle_command_point(self) -> None:
        action = AutomationAction(
            action_type=ActionType.CLICK_UI_BUTTON,
            parameters={"button_ref": "pet_battle_command_bar.defend"},
        )

        result = self.executor.execute(action, self.window_session, self.input_gateway)

        self.assertTrue(result.success)
        self.assertEqual([("click", (1300, 455))], self.input_gateway.operations)

    def test_recover_action_focuses_and_waits(self) -> None:
        action = AutomationAction(
            action_type=ActionType.RECOVER,
            parameters={"wait_seconds": 0.5},
        )

        result = self.executor.execute(action, self.window_session, self.input_gateway)

        self.assertEqual("RECOVER", result.action_type)
        self.assertEqual([("wait", 0.5)], self.input_gateway.operations)

    def test_missing_required_point_raises(self) -> None:
        action = AutomationAction(action_type=ActionType.SELECT_TARGET)

        with self.assertRaises(ActionTranslationError):
            self.executor.execute(action, self.window_session, self.input_gateway)


if __name__ == "__main__":
    unittest.main()
