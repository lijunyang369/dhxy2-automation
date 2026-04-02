from __future__ import annotations

from src.domain import AutomationContext, BattleObservation, BattleState


class TransitionGuard:
    _ALLOWED_TRANSITIONS: dict[BattleState, set[BattleState]] = {
        BattleState.OUT_OF_BATTLE: {
            BattleState.OUT_OF_BATTLE,
            BattleState.BATTLE_ENTERING,
            BattleState.RECOVERING,
        },
        BattleState.BATTLE_ENTERING: {
            BattleState.BATTLE_ENTERING,
            BattleState.BATTLE_READY,
            BattleState.ROUND_ACTIONABLE,
            BattleState.RECOVERING,
            BattleState.OUT_OF_BATTLE,
        },
        BattleState.BATTLE_READY: {
            BattleState.BATTLE_READY,
            BattleState.ROUND_ACTIONABLE,
            BattleState.RECOVERING,
            BattleState.OUT_OF_BATTLE,
        },
        BattleState.ROUND_ACTIONABLE: {
            BattleState.ROUND_ACTIONABLE,
            BattleState.ACTION_EXECUTING,
            BattleState.BATTLE_SETTLING,
            BattleState.OUT_OF_BATTLE,
            BattleState.RECOVERING,
        },
        BattleState.ACTION_EXECUTING: {
            BattleState.ACTION_EXECUTING,
            BattleState.ROUND_WAITING,
            BattleState.RECOVERING,
        },
        BattleState.ROUND_WAITING: {
            BattleState.ROUND_WAITING,
            BattleState.ROUND_ACTIONABLE,
            BattleState.BATTLE_SETTLING,
            BattleState.OUT_OF_BATTLE,
            BattleState.RECOVERING,
        },
        BattleState.BATTLE_SETTLING: {
            BattleState.BATTLE_SETTLING,
            BattleState.BATTLE_FINISHED,
            BattleState.RECOVERING,
        },
        BattleState.BATTLE_FINISHED: {
            BattleState.BATTLE_FINISHED,
            BattleState.OUT_OF_BATTLE,
            BattleState.RECOVERING,
        },
        BattleState.RECOVERING: {
            BattleState.RECOVERING,
            BattleState.OUT_OF_BATTLE,
            BattleState.BATTLE_ENTERING,
            BattleState.BATTLE_READY,
            BattleState.ROUND_ACTIONABLE,
            BattleState.BATTLE_SETTLING,
            BattleState.FAILED,
        },
        BattleState.FAILED: {BattleState.FAILED},
    }

    def can_transit(
        self,
        from_state: BattleState,
        to_state: BattleState,
        observation: BattleObservation,
        context: AutomationContext,
    ) -> bool:
        allowed_states = self._ALLOWED_TRANSITIONS.get(from_state, {from_state})
        if to_state not in allowed_states:
            return False

        if to_state == BattleState.ROUND_ACTIONABLE:
            return observation.round_timer_visible or observation.action_prompt_visible or observation.skill_panel_visible

        if to_state == BattleState.BATTLE_FINISHED:
            return observation.settlement_visible

        if to_state == BattleState.RECOVERING:
            return observation.recovery_required

        if to_state == BattleState.FAILED:
            return context.recovery_count > 0

        return True
