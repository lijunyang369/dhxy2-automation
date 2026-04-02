from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from src.domain import AutomationAction, AutomationContext, ActionType, BattleObservation, BattleState, TransitionResult
from src.runtime import RuntimeSession


def build_observation() -> BattleObservation:
    return BattleObservation(
        battle_ui_visible=True,
        action_prompt_visible=True,
        skill_panel_visible=True,
        target_select_visible=False,
        settlement_visible=False,
        window_alive=True,
        window_focused=True,
        frame_timestamp=datetime.now(timezone.utc),
        frame_hash="frame-hash",
        confidence_summary=0.95,
    )


class RuntimeSessionTestCase(unittest.TestCase):
    def test_runtime_session_creates_artifact_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = AutomationContext(instance_id="instance-1", battle_session_id="battle-1")
            session = RuntimeSession.create(Path(temp_dir), context)

            self.assertTrue(session.artifacts.session_paths.screenshots.exists())
            self.assertTrue(session.artifacts.session_paths.logs.exists())
            self.assertTrue(session.artifacts.session_paths.observations.exists())
            self.assertTrue(session.artifacts.session_paths.actions.exists())

    def test_record_observation_and_action_persist_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = AutomationContext(instance_id="instance-1", battle_session_id="battle-1", state=BattleState.ROUND_ACTIONABLE)
            session = RuntimeSession.create(Path(temp_dir), context)
            observation = build_observation()
            action = AutomationAction(action_type=ActionType.CAST_SKILL, target="enemy_front")

            session.record_observation(observation)
            session.record_action(action, reason="priority_skill")
            session.artifacts.save_frame(Image.new("RGB", (50, 50), color="black"))

            observation_files = list(session.artifacts.session_paths.observations.glob("observation_*.json"))
            action_files = list(session.artifacts.session_paths.actions.glob("action_*.json"))
            screenshot_files = list(session.artifacts.session_paths.screenshots.glob("frame_*.png"))
            runtime_log = session.artifacts.session_paths.logs / "runtime.log"

            self.assertEqual(1, len(observation_files))
            self.assertEqual(1, len(action_files))
            self.assertEqual(1, len(screenshot_files))
            self.assertTrue(runtime_log.exists())

            payload = json.loads(observation_files[0].read_text(encoding="utf-8"))
            self.assertEqual("frame-hash", payload["frame_hash"])

    def test_record_transition_persists_transition_log(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            context = AutomationContext(instance_id="instance-1", battle_session_id="battle-1")
            session = RuntimeSession.create(Path(temp_dir), context)
            transition = TransitionResult(
                from_state=BattleState.OUT_OF_BATTLE,
                to_state=BattleState.BATTLE_ENTERING,
                changed=True,
                reason="observation_resolved",
                observed_state=BattleState.BATTLE_ENTERING,
                details={"round_index": 0},
            )

            session.record_transition(transition)

            transition_files = list(session.artifacts.session_paths.logs.glob("transition_*.json"))
            self.assertEqual(1, len(transition_files))
            payload = json.loads(transition_files[0].read_text(encoding="utf-8"))
            self.assertEqual("BATTLE_ENTERING", payload["to_state"])


if __name__ == "__main__":
    unittest.main()
