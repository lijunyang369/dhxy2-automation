from __future__ import annotations

from src.domain import AutomationAction
from src.executor.exceptions import ActionExecutionError
from src.executor.interfaces import InputGateway
from src.executor.models import ExecutionResult, ExecutionStep, StepType
from src.executor.translator import ActionTranslator
from src.platform import WindowSession


class ActionExecutor:
    def __init__(self, translator: ActionTranslator | None = None) -> None:
        self._translator = translator or ActionTranslator()

    def execute(
        self,
        action: AutomationAction,
        window_session: WindowSession,
        input_gateway: InputGateway,
    ) -> ExecutionResult:
        steps = self._translator.translate(action)
        for step in steps:
            self._run_step(step, window_session, input_gateway)

        return ExecutionResult(
            action_type=action.action_type.value,
            success=True,
            steps=steps,
            message="action executed",
        )

    def _run_step(
        self,
        step: ExecutionStep,
        window_session: WindowSession,
        input_gateway: InputGateway,
    ) -> None:
        if step.step_type == StepType.FOCUS_WINDOW:
            window_session.focus()
            return

        if step.step_type == StepType.CLICK:
            point = step.payload.get("point")
            if point is None or len(point) != 2:
                raise ActionExecutionError("click step requires a 2D point")
            input_gateway.click(int(point[0]), int(point[1]))
            return

        if step.step_type == StepType.PRESS_KEY:
            key = step.payload.get("key")
            if not key:
                raise ActionExecutionError("press_key step requires a key")
            input_gateway.press_key(str(key))
            return

        if step.step_type == StepType.WAIT:
            seconds = float(step.payload.get("seconds", 0.0))
            input_gateway.wait(seconds)
            return

        raise ActionExecutionError(f"unsupported step type={step.step_type}")
