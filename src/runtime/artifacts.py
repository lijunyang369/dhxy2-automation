from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from src.domain import AutomationAction, BattleObservation, TransitionResult


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def timestamp_slug(value: datetime | None = None) -> str:
    current = value or utc_now()
    return current.strftime("%Y%m%dT%H%M%S%fZ")


@dataclass(frozen=True)
class SessionPaths:
    root: Path
    screenshots: Path
    annotated: Path
    logs: Path
    observations: Path
    actions: Path

    @classmethod
    def create(cls, runs_root: Path, instance_id: str, battle_session_id: str) -> "SessionPaths":
        session_root = runs_root / instance_id / battle_session_id
        paths = cls(
            root=session_root,
            screenshots=session_root / "screenshots",
            annotated=session_root / "annotated",
            logs=session_root / "logs",
            observations=session_root / "observations",
            actions=session_root / "actions",
        )
        for path in paths.__dict__.values():
            path.mkdir(parents=True, exist_ok=True)
        return paths


class ArtifactWriter:
    def __init__(self, session_paths: SessionPaths) -> None:
        self._paths = session_paths

    @property
    def session_paths(self) -> SessionPaths:
        return self._paths

    def save_frame(self, image: Image.Image, timestamp: datetime | None = None, prefix: str = "frame") -> Path:
        file_path = self._paths.screenshots / f"{prefix}_{timestamp_slug(timestamp)}.png"
        image.save(file_path)
        return file_path

    def save_observation(self, observation: BattleObservation) -> Path:
        payload = {
            "frame_timestamp": observation.frame_timestamp.isoformat(),
            "frame_hash": observation.frame_hash,
            "battle_ui_visible": observation.battle_ui_visible,
            "action_prompt_visible": observation.action_prompt_visible,
            "skill_panel_visible": observation.skill_panel_visible,
            "target_select_visible": observation.target_select_visible,
            "settlement_visible": observation.settlement_visible,
            "window_alive": observation.window_alive,
            "window_focused": observation.window_focused,
            "confidence_summary": observation.confidence_summary,
            "last_action_feedback": observation.last_action_feedback,
            "anomaly_reason": observation.anomaly_reason,
            "named_regions": observation.named_regions,
            "matches": [
                {
                    "template_id": match.template_id,
                    "confidence": match.confidence,
                    "region_name": match.region_name,
                    "bounds": match.bounds,
                    "note": match.note,
                }
                for match in observation.matches
            ],
        }
        file_path = self._paths.observations / f"observation_{timestamp_slug(observation.frame_timestamp)}.json"
        file_path.write_text(__import__('json').dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return file_path

    def save_action(self, action: AutomationAction, reason: str, timestamp: datetime | None = None) -> Path:
        current = timestamp or utc_now()
        payload = {
            "timestamp": current.isoformat(),
            "action_type": action.action_type.value,
            "target": action.target,
            "parameters": action.parameters,
            "reason": reason,
        }
        file_path = self._paths.actions / f"action_{timestamp_slug(current)}.json"
        file_path.write_text(__import__('json').dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return file_path

    def save_transition(self, transition: TransitionResult) -> Path:
        payload = {
            "timestamp": transition.timestamp.isoformat(),
            "from_state": transition.from_state.value,
            "to_state": transition.to_state.value,
            "changed": transition.changed,
            "reason": transition.reason,
            "observed_state": transition.observed_state.value,
            "details": transition.details,
        }
        file_path = self._paths.logs / f"transition_{timestamp_slug(transition.timestamp)}.json"
        file_path.write_text(__import__('json').dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        return file_path
