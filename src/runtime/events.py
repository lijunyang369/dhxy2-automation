from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeEventType(str, Enum):
    STATE_ENTERED = "state_entered"
    STATE_EXITED = "state_exited"
    TRANSITION_APPLIED = "transition_applied"
    TRANSITION_REJECTED = "transition_rejected"
    ACTION_STARTED = "action_started"
    ACTION_FINISHED = "action_finished"
    ACTION_TIMEOUT = "action_timeout"
    RECOVERY_STARTED = "recovery_started"
    RECOVERY_FINISHED = "recovery_finished"
    RECOVERY_FAILED = "recovery_failed"


@dataclass(frozen=True)
class RuntimeEvent:
    event_type: RuntimeEventType
    instance_id: str
    battle_session_id: str
    state: str
    message: str
    timestamp: datetime = field(default_factory=utc_now)
    details: dict[str, Any] = field(default_factory=dict)
