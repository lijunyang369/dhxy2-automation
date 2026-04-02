from __future__ import annotations

from dataclasses import dataclass

from src.domain import ActionPlan, ActionType, BattleObservation
from src.perception import BattleButtonSemanticCatalog


@dataclass(frozen=True)
class ActionFeedbackDecision:
    accepted: bool
    reason: str
    verified_button_ref: str | None = None


class ActionFeedbackVerifier:
    def __init__(self, semantic_catalog: BattleButtonSemanticCatalog | None = None) -> None:
        self._semantic_catalog = semantic_catalog

    def verify_plan(
        self,
        plan: ActionPlan,
        before: BattleObservation,
        after: BattleObservation,
    ) -> ActionFeedbackDecision:
        if self._semantic_catalog is None:
            return ActionFeedbackDecision(
                accepted=True,
                reason="semantic_catalog_unavailable",
            )

        verifiable_button_refs = [
            str(action.parameters["button_ref"])
            for action in plan.actions
            if action.action_type == ActionType.CLICK_UI_BUTTON and action.parameters.get("button_ref")
        ]
        for action in reversed(plan.actions):
            if action.action_type != ActionType.CLICK_UI_BUTTON:
                continue
            button_ref = action.parameters.get("button_ref")
            if not button_ref:
                continue
            if before.battle_ui_visible and not after.battle_ui_visible:
                return ActionFeedbackDecision(
                    accepted=True,
                    reason="battle_scene_switched_after_action",
                    verified_button_ref=str(button_ref),
                )
            if (
                before.round_number is not None
                and after.round_number is not None
                and after.round_number != before.round_number
            ):
                return ActionFeedbackDecision(
                    accepted=True,
                    reason="round_number_changed_after_action",
                    verified_button_ref=str(button_ref),
                )
            if before.round_timer_visible and not after.round_timer_visible:
                return ActionFeedbackDecision(
                    accepted=True,
                    reason="round_timer_disappeared_after_action",
                    verified_button_ref=str(button_ref),
                )
            rule = self._semantic_catalog.get(str(button_ref))
            if rule is None:
                return ActionFeedbackDecision(
                    accepted=True,
                    reason="semantic_rule_missing",
                    verified_button_ref=str(button_ref),
                )
            if rule.verification_status != "ready":
                return ActionFeedbackDecision(
                    accepted=True,
                    reason=f"semantic_rule_not_ready:{rule.verification_status}",
                    verified_button_ref=str(button_ref),
                )
            if before.round_timer_visible and not before.action_prompt_visible:
                return ActionFeedbackDecision(
                    accepted=True,
                    reason="round_timer_visible_before_click",
                    verified_button_ref=str(button_ref),
                )
            result = self._semantic_catalog.verify(str(button_ref), before, after)
            if (
                not result.confirmed
                and len(verifiable_button_refs) > 1
                and before.action_prompt_visible
                and after.action_prompt_visible
                and before.frame_hash != after.frame_hash
                and after.battle_ui_visible
            ):
                return ActionFeedbackDecision(
                    accepted=True,
                    reason="next_round_prompt_reappeared_after_multi_action_plan",
                    verified_button_ref=str(button_ref),
                )
            return ActionFeedbackDecision(
                accepted=result.confirmed,
                reason=result.reason,
                verified_button_ref=str(button_ref),
            )

        return ActionFeedbackDecision(
            accepted=True,
            reason="no_verifiable_click_ui_button",
        )
