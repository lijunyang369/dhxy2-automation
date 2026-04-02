from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.app import ActionFeedbackVerifier
from src.domain import ActionPlan, ActionType, AutomationAction, BattleObservation, MatchResult
from src.perception import BattleButtonSemanticCatalog
from tests.smoke._paths import CONFIGS_ROOT


def build_observation(*template_ids: str) -> BattleObservation:
    return BattleObservation(
        battle_ui_visible=True,
        action_prompt_visible="battle_action_prompt" in template_ids,
        skill_panel_visible="battle_skill_bar" in template_ids,
        target_select_visible="battle_target_panel" in template_ids,
        settlement_visible=False,
        window_alive=True,
        window_focused=True,
        frame_timestamp=datetime.now(timezone.utc),
        frame_hash="frame-hash",
        confidence_summary=0.95,
        matches=tuple(
            MatchResult(template_id=template_id, confidence=0.99, region_name="test")
            for template_id in template_ids
        ),
    )


class ActionFeedbackVerifierTestCase(unittest.TestCase):
    def setUp(self) -> None:
        catalog = BattleButtonSemanticCatalog.load(CONFIGS_ROOT / "ui" / "battle-button-semantics.json")
        self.verifier = ActionFeedbackVerifier(catalog)

    def test_verify_plan_confirms_ready_defend_button(self) -> None:
        plan = ActionPlan(
            actions=(
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "battle_command_bar.defend"},
                ),
            ),
            reason="defend",
        )

        decision = self.verifier.verify_plan(
            plan=plan,
            before=build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar"),
            after=build_observation("battle_ui", "battle_skill_bar"),
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("battle_command_bar.defend", decision.verified_button_ref)

    def test_verify_plan_accepts_when_round_timer_disappears(self) -> None:
        plan = ActionPlan(
            actions=(
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "battle_command_bar.defend"},
                ),
            ),
            reason="defend",
        )

        decision = self.verifier.verify_plan(
            plan=plan,
            before=build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar"),
            after=build_observation("battle_skill_bar"),
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("round_timer_disappeared_after_action", decision.reason)
        self.assertEqual("battle_command_bar.defend", decision.verified_button_ref)

    def test_verify_plan_rejects_when_ready_rule_fails(self) -> None:
        plan = ActionPlan(
            actions=(
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "battle_command_bar.defend"},
                ),
            ),
            reason="defend",
        )

        decision = self.verifier.verify_plan(
            plan=plan,
            before=build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar"),
            after=build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar"),
        )

        self.assertFalse(decision.accepted)
        self.assertIn("still present", decision.reason)

    def test_verify_plan_confirms_ready_escape_button(self) -> None:
        plan = ActionPlan(
            actions=(
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "character_battle_command_bar.escape"},
                ),
            ),
            reason="escape",
        )

        decision = self.verifier.verify_plan(
            plan=plan,
            before=build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar"),
            after=build_observation("battle_ui", "battle_skill_bar"),
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("character_battle_command_bar.escape", decision.verified_button_ref)

    def test_verify_plan_accepts_next_round_prompt_for_multi_action_plan(self) -> None:
        plan = ActionPlan(
            actions=(
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "battle_command_bar.defend"},
                ),
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "pet_battle_command_bar.defend"},
                ),
            ),
            reason="round1_character_defend_pet_defend",
        )

        decision = self.verifier.verify_plan(
            plan=plan,
            before=BattleObservation(
                battle_ui_visible=True,
                action_prompt_visible=True,
                skill_panel_visible=True,
                target_select_visible=False,
                settlement_visible=False,
                window_alive=True,
                window_focused=True,
                frame_timestamp=datetime.now(timezone.utc),
                frame_hash="frame-before",
                confidence_summary=0.95,
                matches=(
                    MatchResult(template_id="battle_ui", confidence=0.99, region_name="test"),
                    MatchResult(template_id="battle_action_prompt", confidence=0.99, region_name="test"),
                ),
            ),
            after=BattleObservation(
                battle_ui_visible=True,
                action_prompt_visible=True,
                skill_panel_visible=True,
                target_select_visible=False,
                settlement_visible=False,
                window_alive=True,
                window_focused=True,
                frame_timestamp=datetime.now(timezone.utc),
                frame_hash="frame-after",
                confidence_summary=0.95,
                matches=(
                    MatchResult(template_id="battle_ui", confidence=0.99, region_name="test"),
                    MatchResult(template_id="battle_action_prompt", confidence=0.99, region_name="test"),
                ),
            ),
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("next_round_prompt_reappeared_after_multi_action_plan", decision.reason)
        self.assertEqual("pet_battle_command_bar.defend", decision.verified_button_ref)

    def test_verify_plan_accepts_when_round_timer_is_visible_before_click(self) -> None:
        plan = ActionPlan(
            actions=(
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "character_battle_command_bar.escape"},
                ),
            ),
            reason="escape",
        )

        decision = self.verifier.verify_plan(
            plan=plan,
            before=build_observation("battle_ui", "battle_skill_bar"),
            after=build_observation("battle_ui", "battle_skill_bar"),
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("round_timer_visible_before_click", decision.reason)
        self.assertEqual("character_battle_command_bar.escape", decision.verified_button_ref)


if __name__ == "__main__":
    unittest.main()
