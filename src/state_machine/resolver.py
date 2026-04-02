from __future__ import annotations

from dataclasses import dataclass

from src.domain import AutomationContext, BattleObservation, BattleState


@dataclass(frozen=True)
class StateResolverConfig:
    enter_stable_frames: int = 2
    settle_stable_frames: int = 2


class StateResolver:
    def __init__(self, config: StateResolverConfig | None = None) -> None:
        self._config = config or StateResolverConfig()

    def resolve(
        self,
        observation: BattleObservation,
        context: AutomationContext,
    ) -> BattleState:
        if observation.recovery_required:
            return BattleState.RECOVERING

        if observation.settlement_visible:
            if context.state in {BattleState.BATTLE_SETTLING, BattleState.BATTLE_FINISHED}:
                return BattleState.BATTLE_FINISHED
            return BattleState.BATTLE_SETTLING

        if not observation.battle_ui_visible:
            return BattleState.OUT_OF_BATTLE

        if observation.round_timer_visible or observation.action_prompt_visible or observation.skill_panel_visible:
            return BattleState.ROUND_ACTIONABLE

        if context.state == BattleState.ACTION_EXECUTING:
            return BattleState.ACTION_EXECUTING

        if context.state == BattleState.ROUND_WAITING:
            return BattleState.ROUND_WAITING

        if context.state == BattleState.BATTLE_ENTERING:
            return BattleState.BATTLE_READY

        return BattleState.BATTLE_ENTERING
