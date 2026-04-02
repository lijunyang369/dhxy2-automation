from __future__ import annotations

from dataclasses import dataclass, field

from src.domain import ActionType


@dataclass(frozen=True)
class FixedActionRule:
    action_type: ActionType
    reason: str
    target: str | None = None
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class ScriptedActionRule:
    action_type: ActionType
    target: str | None = None
    parameters: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ScriptedRoundRule:
    reason: str
    actions: tuple[ScriptedActionRule, ...]
