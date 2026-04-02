from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.domain import AutomationContext, AutomationAction, BattleObservation, TransitionResult
from src.runtime.artifacts import ArtifactWriter, SessionPaths
from src.runtime.events import RuntimeEvent, RuntimeEventType
from src.runtime.logger import RuntimeLogger


@dataclass
class RuntimeSession:
    context: AutomationContext
    artifacts: ArtifactWriter
    logger: RuntimeLogger

    @classmethod
    def create(
        cls,
        runs_root: Path,
        context: AutomationContext,
    ) -> "RuntimeSession":
        paths = SessionPaths.create(runs_root=runs_root, instance_id=context.instance_id, battle_session_id=context.battle_session_id)
        return cls(
            context=context,
            artifacts=ArtifactWriter(paths),
            logger=RuntimeLogger(paths.logs),
        )

    def record_observation(self, observation: BattleObservation) -> None:
        self.artifacts.save_observation(observation)
        self.logger.log(
            RuntimeEvent(
                event_type=RuntimeEventType.TRANSITION_APPLIED,
                instance_id=self.context.instance_id,
                battle_session_id=self.context.battle_session_id,
                state=self.context.state.value,
                message="observation recorded",
                details={"frame_hash": observation.frame_hash},
            )
        )

    def record_transition(self, transition: TransitionResult) -> None:
        self.artifacts.save_transition(transition)
        self.logger.log(
            RuntimeEvent(
                event_type=RuntimeEventType.TRANSITION_APPLIED if transition.changed else RuntimeEventType.TRANSITION_REJECTED,
                instance_id=self.context.instance_id,
                battle_session_id=self.context.battle_session_id,
                state=transition.to_state.value,
                message=transition.reason,
                details=transition.details,
            )
        )

    def record_action(self, action: AutomationAction, reason: str) -> None:
        self.artifacts.save_action(action, reason=reason)
        self.logger.log(
            RuntimeEvent(
                event_type=RuntimeEventType.ACTION_STARTED,
                instance_id=self.context.instance_id,
                battle_session_id=self.context.battle_session_id,
                state=self.context.state.value,
                message=reason,
                details={
                    "action_type": action.action_type.value,
                    "target": action.target,
                },
            )
        )
