from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.domain import ActionPlan, ActionType, AutomationAction, AutomationContext, BattleObservation, BattleState
from src.state_machine import BattleStateMachine


def build_observation(**overrides: object) -> BattleObservation:
    payload = {
        "battle_ui_visible": False,
        "action_prompt_visible": False,
        "skill_panel_visible": False,
        "target_select_visible": False,
        "settlement_visible": False,
        "window_alive": True,
        "window_focused": True,
        "frame_timestamp": datetime.now(timezone.utc),
        "frame_hash": "frame-hash",
        "confidence_summary": 0.95,
    }
    payload.update(overrides)
    return BattleObservation(**payload)


class BattleStateMachineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.machine = BattleStateMachine()
        self.context = AutomationContext(
            instance_id="instance-1",
            battle_session_id="battle-1",
        )

    def test_enters_battle_after_stable_frames(self) -> None:
        first = self.machine.tick(build_observation(battle_ui_visible=True), self.context)
        second = self.machine.tick(
            build_observation(battle_ui_visible=True, frame_hash="frame-hash-2"),
            self.context,
        )

        self.assertFalse(first.changed)
        self.assertEqual(BattleState.OUT_OF_BATTLE, self.context.previous_state)
        self.assertTrue(second.changed)
        self.assertEqual(BattleState.BATTLE_ENTERING, second.to_state)
        self.assertEqual(BattleState.BATTLE_ENTERING, self.context.state)

    def test_round_actionable_to_round_waiting(self) -> None:
        self.context.state = BattleState.ROUND_ACTIONABLE
        self.context.previous_stable_state = BattleState.ROUND_ACTIONABLE
        plan = ActionPlan(
            actions=(AutomationAction(action_type=ActionType.CAST_SKILL, target="enemy_front"),),
            reason="priority_skill",
        )

        started = self.machine.begin_action(plan, self.context)
        finished = self.machine.complete_action(self.context, accepted_by_ui=True)

        self.assertTrue(started.changed)
        self.assertEqual(BattleState.ACTION_EXECUTING, started.to_state)
        self.assertTrue(finished.changed)
        self.assertEqual(BattleState.ROUND_WAITING, finished.to_state)
        self.assertEqual(1, self.context.round_index)
        self.assertIsNone(self.context.current_plan)

    def test_recovery_flow_fails_after_limit(self) -> None:
        self.machine.tick(build_observation(anomaly_reason="window_lost"), self.context)

        self.assertEqual(BattleState.RECOVERING, self.context.state)

        self.machine.mark_recovery_failed(self.context)
        self.machine.mark_recovery_failed(self.context)
        final = self.machine.mark_recovery_failed(self.context)

        self.assertEqual(BattleState.FAILED, final.to_state)
        self.assertEqual(BattleState.FAILED, self.context.state)

    def test_round_waiting_can_exit_directly_when_battle_ui_disappears(self) -> None:
        self.context.state = BattleState.ROUND_WAITING
        self.context.previous_stable_state = BattleState.ROUND_WAITING

        transition = self.machine.tick(build_observation(battle_ui_visible=False), self.context)

        self.assertTrue(transition.changed)
        self.assertEqual(BattleState.OUT_OF_BATTLE, transition.to_state)
        self.assertEqual(BattleState.OUT_OF_BATTLE, self.context.state)

    def test_round_actionable_can_exit_directly_when_battle_ui_disappears(self) -> None:
        self.context.state = BattleState.ROUND_ACTIONABLE
        self.context.previous_stable_state = BattleState.ROUND_ACTIONABLE

        transition = self.machine.tick(build_observation(battle_ui_visible=False), self.context)

        self.assertTrue(transition.changed)
        self.assertEqual(BattleState.OUT_OF_BATTLE, transition.to_state)
        self.assertEqual(BattleState.OUT_OF_BATTLE, self.context.state)


if __name__ == "__main__":
    unittest.main()
