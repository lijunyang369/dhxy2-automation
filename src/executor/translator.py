from __future__ import annotations

from src.domain import ActionType, AutomationAction
from src.executor.button_calibration import ButtonCalibration
from src.executor.exceptions import ActionTranslationError
from src.executor.models import ExecutionStep, StepType


class ActionTranslator:
    def __init__(self, button_calibration: ButtonCalibration | None = None) -> None:
        self._button_calibration = button_calibration

    def translate(self, action: AutomationAction) -> tuple[ExecutionStep, ...]:
        if action.action_type == ActionType.NO_OP:
            return (ExecutionStep(step_type=StepType.FOCUS_WINDOW),)

        if action.action_type == ActionType.CLICK_UI_BUTTON:
            point = self._require_point(action, "button_point", fallback_ref_key="button_ref")
            return (
                ExecutionStep(step_type=StepType.FOCUS_WINDOW),
                ExecutionStep(step_type=StepType.CLICK, payload={"point": point}),
            )

        if action.action_type == ActionType.CAST_SKILL:
            skill_point = self._require_point(action, "skill_point")
            steps = [
                ExecutionStep(step_type=StepType.FOCUS_WINDOW),
                ExecutionStep(step_type=StepType.CLICK, payload={"point": skill_point}),
            ]
            target_point = action.parameters.get("target_point")
            if target_point is not None:
                steps.append(ExecutionStep(step_type=StepType.CLICK, payload={"point": tuple(target_point)}))
            confirm_point = action.parameters.get("confirm_point")
            if confirm_point is not None:
                steps.append(ExecutionStep(step_type=StepType.CLICK, payload={"point": tuple(confirm_point)}))
            return tuple(steps)

        if action.action_type == ActionType.USE_ITEM:
            item_point = self._require_point(action, "item_point")
            steps = [
                ExecutionStep(step_type=StepType.FOCUS_WINDOW),
                ExecutionStep(step_type=StepType.CLICK, payload={"point": item_point}),
            ]
            target_point = action.parameters.get("target_point")
            if target_point is not None:
                steps.append(ExecutionStep(step_type=StepType.CLICK, payload={"point": tuple(target_point)}))
            return tuple(steps)

        if action.action_type == ActionType.SELECT_TARGET:
            target_point = self._require_point(action, "target_point")
            return (
                ExecutionStep(step_type=StepType.FOCUS_WINDOW),
                ExecutionStep(step_type=StepType.CLICK, payload={"point": target_point}),
            )

        if action.action_type == ActionType.CONFIRM_ACTION:
            confirm_point = self._require_point(action, "confirm_point")
            return (
                ExecutionStep(step_type=StepType.FOCUS_WINDOW),
                ExecutionStep(step_type=StepType.CLICK, payload={"point": confirm_point}),
            )

        if action.action_type == ActionType.RECOVER:
            wait_seconds = float(action.parameters.get("wait_seconds", 0.2))
            return (
                ExecutionStep(step_type=StepType.FOCUS_WINDOW),
                ExecutionStep(step_type=StepType.WAIT, payload={"seconds": wait_seconds}),
            )

        raise ActionTranslationError(f"unsupported action type={action.action_type}")

    def _require_point(
        self,
        action: AutomationAction,
        key: str,
        fallback_ref_key: str | None = None,
    ) -> tuple[int, int]:
        point = action.parameters.get(key)
        if point is not None:
            return tuple(point)

        if fallback_ref_key:
            button_ref = action.parameters.get(fallback_ref_key)
            if button_ref is not None:
                return self._resolve_button_ref(str(button_ref))

        raise ActionTranslationError(
            f"action type={action.action_type.value} requires parameter={key}"
        )

    def _resolve_button_ref(self, button_ref: str) -> tuple[int, int]:
        if self._button_calibration is None:
            raise ActionTranslationError(f"button_ref={button_ref} requires button calibration")
        try:
            return self._button_calibration.resolve(button_ref)
        except KeyError as exc:
            raise ActionTranslationError(str(exc)) from exc
