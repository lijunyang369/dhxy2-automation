from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from src.domain.profile_models import CharacterProfile


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class BattleState(str, Enum):
    OUT_OF_BATTLE = "OUT_OF_BATTLE"
    BATTLE_ENTERING = "BATTLE_ENTERING"
    BATTLE_READY = "BATTLE_READY"
    ROUND_ACTIONABLE = "ROUND_ACTIONABLE"
    ACTION_EXECUTING = "ACTION_EXECUTING"
    ROUND_WAITING = "ROUND_WAITING"
    BATTLE_SETTLING = "BATTLE_SETTLING"
    BATTLE_FINISHED = "BATTLE_FINISHED"
    RECOVERING = "RECOVERING"
    FAILED = "FAILED"


class ActionType(str, Enum):
    CAST_SKILL = "CAST_SKILL"
    USE_ITEM = "USE_ITEM"
    SELECT_TARGET = "SELECT_TARGET"
    CONFIRM_ACTION = "CONFIRM_ACTION"
    CLICK_UI_BUTTON = "CLICK_UI_BUTTON"
    RECOVER = "RECOVER"
    NO_OP = "NO_OP"


@dataclass(frozen=True)
class MatchResult:
    template_id: str
    confidence: float
    region_name: str
    bounds: tuple[int, int, int, int] | None = None
    note: str | None = None


@dataclass(frozen=True)
class AutomationAction:
    action_type: ActionType
    target: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionPlan:
    actions: tuple[AutomationAction, ...]
    reason: str

    def is_empty(self) -> bool:
        return not self.actions


@dataclass(frozen=True)
class BattleObservation:
    battle_ui_visible: bool
    action_prompt_visible: bool
    skill_panel_visible: bool
    target_select_visible: bool
    settlement_visible: bool
    window_alive: bool
    window_focused: bool
    frame_timestamp: datetime
    frame_hash: str
    confidence_summary: float
    round_indicator_visible: bool = False
    round_number: int | None = None
    round_digits: tuple[str, ...] = ()
    round_recognition_reason: str = ""
    round_recognition_confidence: float = 0.0
    matches: tuple[MatchResult, ...] = ()
    named_regions: dict[str, tuple[int, int, int, int]] = field(default_factory=dict)
    last_action_feedback: str | None = None
    anomaly_reason: str | None = None

    @property
    def recovery_required(self) -> bool:
        return (not self.window_alive) or (self.anomaly_reason is not None)

    @property
    def round_timer_visible(self) -> bool:
        return self.round_indicator_visible or any(match.template_id == "battle_ui" for match in self.matches)

    @property
    def round_number_text(self) -> str:
        if self.round_digits:
            return "".join(self.round_digits)
        if self.round_number is not None:
            return str(self.round_number)
        return ""


@dataclass
class AutomationContext:
    instance_id: str
    battle_session_id: str
    state: BattleState = BattleState.OUT_OF_BATTLE
    previous_state: BattleState = BattleState.OUT_OF_BATTLE
    previous_stable_state: BattleState = BattleState.OUT_OF_BATTLE
    round_index: int = 0
    recovery_count: int = 0
    stable_frame_count: int = 0
    last_observed_state: BattleState | None = None
    current_plan: ActionPlan | None = None
    last_action_at: datetime | None = None
    character_profile: CharacterProfile | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TransitionResult:
    from_state: BattleState
    to_state: BattleState
    changed: bool
    reason: str
    observed_state: BattleState
    timestamp: datetime = field(default_factory=utc_now)
    details: dict[str, Any] = field(default_factory=dict)


class DomainError(Exception):
    pass


class InvalidStateTransitionError(DomainError):
    pass
