from __future__ import annotations

from dataclasses import dataclass

from src.domain import (
    ActionPlan,
    AutomationContext,
    BattleObservation,
    BattleState,
    InvalidStateTransitionError,
    TransitionResult,
)
from src.state_machine.guards import TransitionGuard
from src.state_machine.resolver import StateResolver, StateResolverConfig


@dataclass(frozen=True)
class BattleStateMachineConfig:
    enter_stable_frames: int = 2
    settle_stable_frames: int = 2
    max_recovery_attempts: int = 3


class BattleStateMachine:
    def __init__(
        self,
        resolver: StateResolver | None = None,
        guard: TransitionGuard | None = None,
        config: BattleStateMachineConfig | None = None,
    ) -> None:
        self._config = config or BattleStateMachineConfig()
        self._resolver = resolver or StateResolver(
            StateResolverConfig(
                enter_stable_frames=self._config.enter_stable_frames,
                settle_stable_frames=self._config.settle_stable_frames,
            )
        )
        self._guard = guard or TransitionGuard()

    def tick(
        self,
        observation: BattleObservation,
        context: AutomationContext,
    ) -> TransitionResult:
        observed_state = self._resolver.resolve(observation, context)
        target_state = self._select_target_state(observed_state, context)

        if not self._guard.can_transit(context.state, target_state, observation, context):
            return self._build_result(
                context=context,
                from_state=context.state,
                target_state=context.state,
                observed_state=observed_state,
                changed=False,
                reason="transition_guard_rejected",
            )

        return self._apply_transition(
            context=context,
            observation=observation,
            target_state=target_state,
            observed_state=observed_state,
            reason="observation_resolved",
        )

    def begin_action(self, plan: ActionPlan, context: AutomationContext) -> TransitionResult:
        if context.state != BattleState.ROUND_ACTIONABLE:
            raise InvalidStateTransitionError(f"cannot begin action from state={context.state}")

        context.current_plan = plan
        return self._apply_transition(
            context=context,
            observation=None,
            target_state=BattleState.ACTION_EXECUTING,
            observed_state=BattleState.ACTION_EXECUTING,
            reason="action_plan_started",
        )

    def complete_action(self, context: AutomationContext, accepted_by_ui: bool) -> TransitionResult:
        if context.state != BattleState.ACTION_EXECUTING:
            raise InvalidStateTransitionError(f"cannot complete action from state={context.state}")

        next_state = BattleState.ROUND_WAITING if accepted_by_ui else BattleState.RECOVERING
        return self._apply_transition(
            context=context,
            observation=None,
            target_state=next_state,
            observed_state=next_state,
            reason="action_feedback_received" if accepted_by_ui else "action_feedback_missing",
        )

    def mark_recovery_failed(self, context: AutomationContext) -> TransitionResult:
        context.recovery_count += 1
        target_state = (
            BattleState.FAILED
            if context.recovery_count >= self._config.max_recovery_attempts
            else BattleState.RECOVERING
        )
        return self._apply_transition(
            context=context,
            observation=None,
            target_state=target_state,
            observed_state=target_state,
            reason="recovery_attempt_recorded",
        )

    def _select_target_state(self, observed_state: BattleState, context: AutomationContext) -> BattleState:
        if observed_state == BattleState.RECOVERING:
            return BattleState.RECOVERING

        stable_states = {
            BattleState.BATTLE_ENTERING: self._config.enter_stable_frames,
            BattleState.BATTLE_SETTLING: self._config.settle_stable_frames,
        }
        required_frames = stable_states.get(observed_state)

        if required_frames is None:
            context.stable_frame_count = 0
            context.last_observed_state = observed_state
            return observed_state

        if context.last_observed_state == observed_state:
            context.stable_frame_count += 1
        else:
            context.last_observed_state = observed_state
            context.stable_frame_count = 1

        if context.stable_frame_count >= required_frames:
            return observed_state

        return context.state

    def _apply_transition(
        self,
        context: AutomationContext,
        observation: BattleObservation | None,
        target_state: BattleState,
        observed_state: BattleState,
        reason: str,
    ) -> TransitionResult:
        previous_state = context.state
        changed = previous_state != target_state

        if changed:
            context.previous_state = previous_state
            context.state = target_state
            if target_state not in {BattleState.RECOVERING, BattleState.FAILED}:
                context.previous_stable_state = target_state
            if target_state == BattleState.RECOVERING:
                context.recovery_count += 1
            if target_state == BattleState.ROUND_WAITING:
                context.round_index += 1
                context.current_plan = None

        if observation is not None:
            context.metadata["last_frame_hash"] = observation.frame_hash

        context.last_observed_state = observed_state
        return self._build_result(
            context=context,
            from_state=previous_state,
            target_state=target_state,
            observed_state=observed_state,
            changed=changed,
            reason=reason,
        )

    def _build_result(
        self,
        context: AutomationContext,
        from_state: BattleState,
        target_state: BattleState,
        observed_state: BattleState,
        changed: bool,
        reason: str,
    ) -> TransitionResult:
        return TransitionResult(
            from_state=from_state,
            to_state=target_state,
            changed=changed,
            reason=reason,
            observed_state=observed_state,
            details={
                "instance_id": context.instance_id,
                "battle_session_id": context.battle_session_id,
                "round_index": context.round_index,
                "recovery_count": context.recovery_count,
            },
        )


