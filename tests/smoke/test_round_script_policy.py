from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from src.app import BattleAutomationApp, CharacterProfileLoader
from src.domain import ActionType, AutomationContext, BattleObservation, BattleState
from src.executor import ActionExecutor, ActionTranslator, ButtonCalibration
from src.platform import Rect, WindowSession
from src.policy import ScriptedActionRule, ScriptedRoundPolicy, ScriptedRoundRule
from src.runtime import RuntimeSession
from src.state_machine import BattleStateMachine
from tests.smoke._paths import CONFIGS_ROOT


class SequenceObservationProvider:
    def __init__(self, observations: list[BattleObservation]) -> None:
        self._observations = observations
        self._index = 0

    def observe(self, window_session: WindowSession) -> BattleObservation:
        del window_session
        if self._index >= len(self._observations):
            return self._observations[-1]
        observation = self._observations[self._index]
        self._index += 1
        return observation


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


def build_observation(
    *,
    battle_ui_visible: bool,
    action_prompt_visible: bool,
    skill_panel_visible: bool,
    settlement_visible: bool = False,
    round_number: int | None = 1,
) -> BattleObservation:
    return BattleObservation(
        battle_ui_visible=battle_ui_visible,
        action_prompt_visible=action_prompt_visible,
        skill_panel_visible=skill_panel_visible,
        target_select_visible=False,
        settlement_visible=settlement_visible,
        window_alive=True,
        window_focused=True,
        frame_timestamp=datetime.now(timezone.utc),
        frame_hash="frame-hash",
        confidence_summary=0.95,
        round_indicator_visible=round_number is not None,
        round_number=round_number,
        round_digits=() if round_number is None else tuple(str(round_number)),
        round_recognition_reason="test",
        round_recognition_confidence=0.95 if round_number is not None else 0.0,
    )


class ScriptedRoundPolicyFlowTestCase(unittest.TestCase):
    def test_validates_basic_two_round_battle_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = AutomationContext(
                instance_id="instance-1",
                battle_session_id="battle-flow-1",
                state=BattleState.ROUND_ACTIONABLE,
            )
            context.character_profile = CharacterProfileLoader().load(
                CONFIGS_ROOT / "characters" / "mage-default.json"
            )
            calibration = ButtonCalibration.load(CONFIGS_ROOT / "ui" / "button-calibration.json")
            input_gateway = FakeInputGateway()
            policy = ScriptedRoundPolicy(
                rounds=(
                    ScriptedRoundRule(
                        reason="round1_defend_defend",
                        actions=(
                            ScriptedActionRule(
                                action_type=ActionType.CLICK_UI_BUTTON,
                                target="character_battle_command_bar",
                                parameters={"button_ref": "battle_command_bar.defend"},
                            ),
                            ScriptedActionRule(
                                action_type=ActionType.CLICK_UI_BUTTON,
                                target="pet_battle_command_bar",
                                parameters={"button_ref": "pet_battle_command_bar.defend"},
                            ),
                        ),
                    ),
                    ScriptedRoundRule(
                        reason="round2_escape_defend",
                        actions=(
                            ScriptedActionRule(
                                action_type=ActionType.CLICK_UI_BUTTON,
                                target="character_battle_command_bar",
                                parameters={"button_ref": "battle_command_bar.escape"},
                            ),
                            ScriptedActionRule(
                                action_type=ActionType.CLICK_UI_BUTTON,
                                target="pet_battle_command_bar",
                                parameters={"button_ref": "pet_battle_command_bar.defend"},
                            ),
                        ),
                    ),
                )
            )
            app = BattleAutomationApp(
                context=context,
                window_session=WindowSession(handle=1001, gateway=FakeWindowGateway()),
                observation_provider=SequenceObservationProvider(
                    [
                        build_observation(battle_ui_visible=True, action_prompt_visible=True, skill_panel_visible=True),
                        build_observation(
                            battle_ui_visible=True,
                            action_prompt_visible=False,
                            skill_panel_visible=False,
                            round_number=None,
                        ),
                        build_observation(
                            battle_ui_visible=True,
                            action_prompt_visible=False,
                            skill_panel_visible=False,
                            round_number=None,
                        ),
                        build_observation(
                            battle_ui_visible=True,
                            action_prompt_visible=True,
                            skill_panel_visible=True,
                            round_number=2,
                        ),
                        build_observation(
                            battle_ui_visible=False,
                            action_prompt_visible=False,
                            skill_panel_visible=False,
                            round_number=None,
                        ),
                    ]
                ),
                state_machine=BattleStateMachine(),
                policy=policy,
                executor=ActionExecutor(translator=ActionTranslator(button_calibration=calibration)),
                runtime_session=RuntimeSession.create(Path(temp_dir), context),
                input_gateway=input_gateway,
            )

            round1 = app.run_once()
            waiting = app.run_once()
            round2 = app.run_once()
            finished = app.run_once()

            self.assertEqual(2, len(round1.executed_actions))
            self.assertEqual(["CLICK_UI_BUTTON", "CLICK_UI_BUTTON"], [item.action_type for item in round1.executed_actions])
            self.assertEqual(0, len(waiting.executed_actions))
            self.assertEqual(2, len(round2.executed_actions))
            self.assertEqual(BattleState.OUT_OF_BATTLE, app.context.state)
            self.assertEqual(
                [
                    ("click", (1300, 355)),
                    ("click", (1300, 455)),
                    ("click", (1300, 480)),
                    ("click", (1300, 455)),
                ],
                input_gateway.operations,
            )
            self.assertEqual(0, len(finished.executed_actions))


if __name__ == "__main__":
    unittest.main()
