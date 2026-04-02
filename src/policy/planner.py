from __future__ import annotations

from src.domain import ActionPlan, AutomationAction, AutomationContext, BattleObservation, BattleState
from src.policy.context_access import require_character_profile
from src.policy.models import FixedActionRule, PolicyDecision, ScriptedRoundRule


class FixedRulePolicy:
    def __init__(self, primary_rule: FixedActionRule) -> None:
        self._primary_rule = primary_rule

    def evaluate(
        self,
        observation: BattleObservation,
        context: AutomationContext,
    ) -> PolicyDecision:
        if context.character_profile is None:
            return PolicyDecision(allowed=False, reason="character profile is missing")

        if context.state != BattleState.ROUND_ACTIONABLE:
            return PolicyDecision(
                allowed=False,
                reason=f"state {context.state.value} is not actionable",
            )

        if not observation.window_alive:
            return PolicyDecision(allowed=False, reason="window is not alive")

        if not observation.window_focused:
            return PolicyDecision(allowed=False, reason="window is not focused")

        if not observation.round_timer_visible and not observation.action_prompt_visible and not observation.skill_panel_visible:
            return PolicyDecision(allowed=False, reason="action signals are missing")

        return PolicyDecision(allowed=True, reason=self._primary_rule.reason)

    def build_plan(
        self,
        observation: BattleObservation,
        context: AutomationContext,
    ) -> ActionPlan:
        decision = self.evaluate(observation, context)
        if not decision.allowed:
            return ActionPlan(actions=(), reason=decision.reason)

        profile = require_character_profile(context)
        action = AutomationAction(
            action_type=self._primary_rule.action_type,
            target=self._primary_rule.target or profile.default_target_rule,
            parameters=dict(self._primary_rule.parameters),
        )
        return ActionPlan(actions=(action,), reason=decision.reason)


class ScriptedRoundPolicy:
    def __init__(self, rounds: tuple[ScriptedRoundRule, ...]) -> None:
        self._rounds = rounds

    def evaluate(
        self,
        observation: BattleObservation,
        context: AutomationContext,
    ) -> PolicyDecision:
        if context.character_profile is None:
            return PolicyDecision(allowed=False, reason="character profile is missing")

        if context.state != BattleState.ROUND_ACTIONABLE:
            return PolicyDecision(
                allowed=False,
                reason=f"state {context.state.value} is not actionable",
            )

        if not observation.window_alive:
            return PolicyDecision(allowed=False, reason="window is not alive")

        if not observation.window_focused:
            return PolicyDecision(allowed=False, reason="window is not focused")

        if not observation.round_timer_visible and not observation.action_prompt_visible and not observation.skill_panel_visible:
            return PolicyDecision(allowed=False, reason="action signals are missing")

        if context.round_index >= len(self._rounds):
            return PolicyDecision(allowed=False, reason="round script is exhausted")

        return PolicyDecision(allowed=True, reason=self._rounds[context.round_index].reason)

    def build_plan(
        self,
        observation: BattleObservation,
        context: AutomationContext,
    ) -> ActionPlan:
        decision = self.evaluate(observation, context)
        if not decision.allowed:
            return ActionPlan(actions=(), reason=decision.reason)

        profile = require_character_profile(context)
        round_rule = self._rounds[context.round_index]
        actions = tuple(
            AutomationAction(
                action_type=entry.action_type,
                target=entry.target or profile.default_target_rule,
                parameters=dict(entry.parameters),
            )
            for entry in round_rule.actions
        )
        return ActionPlan(actions=actions, reason=round_rule.reason)
