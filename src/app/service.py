from __future__ import annotations

from dataclasses import dataclass

from src.app.action_feedback import ActionFeedbackVerifier
from src.domain import AutomationAction, AutomationContext, BattleObservation, CharacterProfile, TransitionResult
from src.executor import ActionExecutor, ExecutionResult, InputGateway
from src.platform import WindowSession
from src.policy import FixedRulePolicy
from src.runtime import RuntimeSession
from src.state_machine import BattleStateMachine
from src.app.interfaces import ObservationProvider


@dataclass(frozen=True)
class AppTickResult:
    observation: BattleObservation
    feedback_observation: BattleObservation | None
    transitions: tuple[TransitionResult, ...]
    executed_actions: tuple[ExecutionResult, ...]
    planned_actions: tuple[AutomationAction, ...] = ()


class BattleAutomationApp:
    def __init__(
        self,
        context: AutomationContext,
        window_session: WindowSession,
        observation_provider: ObservationProvider,
        state_machine: BattleStateMachine,
        policy: FixedRulePolicy,
        executor: ActionExecutor,
        runtime_session: RuntimeSession,
        input_gateway: InputGateway,
        feedback_verifier: ActionFeedbackVerifier | None = None,
    ) -> None:
        self._context = context
        self._window_session = window_session
        self._observation_provider = observation_provider
        self._state_machine = state_machine
        self._policy = policy
        self._executor = executor
        self._runtime_session = runtime_session
        self._input_gateway = input_gateway
        self._feedback_verifier = feedback_verifier or ActionFeedbackVerifier()

    @property
    def context(self) -> AutomationContext:
        return self._context

    @property
    def window_session(self) -> WindowSession:
        return self._window_session

    @property
    def character_profile(self) -> CharacterProfile | None:
        return self._context.character_profile

    def run_once(self) -> AppTickResult:
        observation = self._observation_provider.observe(self._window_session)
        self._runtime_session.record_observation(observation)

        transitions: list[TransitionResult] = []
        executed_actions: list[ExecutionResult] = []

        state_transition = self._state_machine.tick(observation, self._context)
        self._runtime_session.record_transition(state_transition)
        transitions.append(state_transition)

        plan = self._policy.build_plan(observation, self._context)
        if plan.is_empty():
            return AppTickResult(
                observation=observation,
                feedback_observation=None,
                transitions=tuple(transitions),
                executed_actions=tuple(executed_actions),
                planned_actions=(),
            )

        begin_transition = self._state_machine.begin_action(plan, self._context)
        self._runtime_session.record_transition(begin_transition)
        transitions.append(begin_transition)

        for action in plan.actions:
            self._runtime_session.record_action(action, reason=plan.reason)
            executed_actions.append(
                self._executor.execute(
                    action=action,
                    window_session=self._window_session,
                    input_gateway=self._input_gateway,
                )
            )

        feedback_observation = self._observation_provider.observe(self._window_session)
        self._runtime_session.record_observation(feedback_observation)
        feedback_decision = self._feedback_verifier.verify_plan(
            plan=plan,
            before=observation,
            after=feedback_observation,
        )
        self._context.metadata["last_action_feedback"] = feedback_decision.reason
        finish_transition = self._state_machine.complete_action(
            self._context,
            accepted_by_ui=feedback_decision.accepted,
        )
        self._runtime_session.record_transition(finish_transition)
        transitions.append(finish_transition)

        if observation.battle_ui_visible and not feedback_observation.battle_ui_visible:
            end_transition = self._state_machine.tick(feedback_observation, self._context)
            self._runtime_session.record_transition(end_transition)
            transitions.append(end_transition)

        return AppTickResult(
            observation=observation,
            feedback_observation=feedback_observation,
            transitions=tuple(transitions),
            executed_actions=tuple(executed_actions),
            planned_actions=plan.actions,
        )
