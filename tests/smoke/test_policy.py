from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.app import CharacterProfileLoader
from src.domain import ActionType, AutomationContext, BattleObservation, BattleState
from src.policy import FixedActionRule, FixedRulePolicy, PolicyDecisionError, require_character_profile
from tests.smoke._paths import CONFIGS_ROOT


def build_observation(**overrides: object) -> BattleObservation:
    payload = {
        "battle_ui_visible": True,
        "action_prompt_visible": True,
        "skill_panel_visible": True,
        "target_select_visible": False,
        "settlement_visible": False,
        "window_alive": True,
        "window_focused": True,
        "frame_timestamp": datetime.now(timezone.utc),
        "frame_hash": "frame-hash",
        "confidence_summary": 0.95,
        "round_indicator_visible": True,
        "round_number": 1,
        "round_digits": ("1",),
        "round_recognition_reason": "test",
        "round_recognition_confidence": 0.95,
    }
    payload.update(overrides)
    return BattleObservation(**payload)


class FixedRulePolicyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = FixedRulePolicy(
            FixedActionRule(
                action_type=ActionType.CAST_SKILL,
                reason="fixed_priority_skill",
                target="enemy_front",
                parameters={
                    "skill_point": (100, 200),
                    "target_point": (300, 400),
                    "confirm_point": (500, 600),
                },
            )
        )
        self.context = AutomationContext(
            instance_id="instance-1",
            battle_session_id="battle-1",
            state=BattleState.ROUND_ACTIONABLE,
        )
        self.context.character_profile = CharacterProfileLoader().load(
            CONFIGS_ROOT / "characters" / "mage-default.json"
        )

    def test_build_plan_returns_single_action_when_actionable(self) -> None:
        observation = build_observation()

        plan = self.policy.build_plan(observation, self.context)

        self.assertFalse(plan.is_empty())
        self.assertEqual(ActionType.CAST_SKILL, plan.actions[0].action_type)
        self.assertEqual("enemy_front", plan.actions[0].target)
        self.assertEqual("fixed_priority_skill", plan.reason)

    def test_build_plan_returns_empty_when_state_not_actionable(self) -> None:
        self.context.state = BattleState.ROUND_WAITING
        observation = build_observation()

        plan = self.policy.build_plan(observation, self.context)

        self.assertTrue(plan.is_empty())
        self.assertIn("not actionable", plan.reason)

    def test_build_plan_returns_empty_when_window_not_focused(self) -> None:
        observation = build_observation(window_focused=False)

        plan = self.policy.build_plan(observation, self.context)

        self.assertTrue(plan.is_empty())
        self.assertEqual("window is not focused", plan.reason)

    def test_build_plan_returns_empty_when_character_profile_is_missing(self) -> None:
        self.context.character_profile = None
        observation = build_observation()

        plan = self.policy.build_plan(observation, self.context)

        self.assertTrue(plan.is_empty())
        self.assertEqual("character profile is missing", plan.reason)

    def test_build_plan_falls_back_to_profile_default_target_when_rule_target_is_missing(self) -> None:
        policy = FixedRulePolicy(
            FixedActionRule(
                action_type=ActionType.CAST_SKILL,
                reason="use_default_target_rule",
                target=None,
                parameters={"skill_point": (100, 200)},
            )
        )
        observation = build_observation()

        plan = policy.build_plan(observation, self.context)

        self.assertFalse(plan.is_empty())
        self.assertEqual("enemy_front", plan.actions[0].target)

    def test_require_character_profile_returns_bound_instance_profile(self) -> None:
        resolved = require_character_profile(self.context)

        self.assertEqual("mage-default", resolved.character_id)

    def test_require_character_profile_raises_when_instance_has_no_profile(self) -> None:
        self.context.character_profile = None
        with self.assertRaises(PolicyDecisionError):
            require_character_profile(self.context)


if __name__ == "__main__":
    unittest.main()
