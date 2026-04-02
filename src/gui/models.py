from __future__ import annotations

from dataclasses import dataclass

from src.domain import AutomationAction, BattleObservation, TransitionResult
from src.executor import ExecutionResult


@dataclass(frozen=True)
class ManualProbeArtifacts:
    run_id: str
    handle: int
    client_x: int
    client_y: int
    screen_x: int
    screen_y: int
    before_path: str
    after_path: str
    before_hash: str
    after_hash: str
    frame_changed: bool
    delay_seconds: float
    label: str
    button_ref: str
    status: str = "pending_review"
    notes: str = ""


@dataclass(frozen=True)
class ButtonCalibrationEntry:
    group: str
    name: str
    button_ref: str
    label: str
    x: int
    y: int
    status: str
    notes: str

    @property
    def category(self) -> str:
        if self.group == "battle_command_bar":
            return "character_battle"
        if self.group == "pet_battle_command_bar":
            return "pet_battle"
        return "nonbattle"

    @property
    def section_label(self) -> str:
        if self.category == "character_battle":
            return "角色战斗指令"
        if self.category == "pet_battle":
            return "宠物战斗指令"
        return "非战斗界面"


@dataclass(frozen=True)
class AutoBattleTickReport:
    tick_index: int
    state: str
    round_index: int
    feedback_reason: str
    session_root: str
    runtime_log_path: str
    observation: BattleObservation
    feedback_observation: BattleObservation | None
    transitions: tuple[TransitionResult, ...]
    executed_actions: tuple[ExecutionResult, ...]
    planned_actions: tuple[AutomationAction, ...]
    finished: bool
