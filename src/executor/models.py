from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StepType(str, Enum):
    FOCUS_WINDOW = "FOCUS_WINDOW"
    CLICK = "CLICK"
    PRESS_KEY = "PRESS_KEY"
    WAIT = "WAIT"


@dataclass(frozen=True)
class ExecutionStep:
    step_type: StepType
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionResult:
    action_type: str
    success: bool
    steps: tuple[ExecutionStep, ...]
    message: str
    executed_at: datetime = field(default_factory=utc_now)
