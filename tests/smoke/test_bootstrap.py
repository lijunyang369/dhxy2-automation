from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

from src.app import BootstrapPaths, NoOpInputGateway, build_app
from src.app.bootstrap import _build_feedback_verifier
from src.domain import ActionPlan, BattleObservation
from src.platform import Rect, WindowSession
from tests.smoke._paths import CONFIGS_ROOT


class FakeWindowGateway:
    def is_window(self, handle: int) -> bool:
        return handle == 1001

    def is_window_visible(self, handle: int) -> bool:
        return True

    def get_foreground_window(self) -> int:
        return 1001

    def focus_window(self, handle: int) -> None:
        return None

    def get_window_text(self, handle: int) -> str:
        return "dhxy2"

    def get_class_name(self, handle: int) -> str:
        return "DhxyWindow"

    def get_window_rect(self, handle: int) -> Rect:
        return Rect(0, 0, 1280, 720)

    def get_client_rect(self, handle: int) -> Rect:
        return Rect(8, 32, 1272, 712)

    def capture_rect(self, rect: Rect) -> Image.Image:
        return Image.new("RGB", (rect.width, rect.height), color="black")


def build_observation() -> BattleObservation:
    return BattleObservation(
        battle_ui_visible=True,
        action_prompt_visible=False,
        skill_panel_visible=False,
        target_select_visible=False,
        settlement_visible=False,
        window_alive=True,
        window_focused=True,
        frame_timestamp=datetime.now(timezone.utc),
        frame_hash="frame-hash",
        confidence_summary=0.95,
    )


class BootstrapTestCase(unittest.TestCase):
    def test_build_feedback_verifier_without_semantic_config_falls_back_to_default_verifier(self) -> None:
        verifier = _build_feedback_verifier({})

        decision = verifier.verify_plan(
            ActionPlan(actions=(), reason="no-actions"),
            build_observation(),
            build_observation(),
        )

        self.assertTrue(decision.accepted)
        self.assertEqual("semantic_catalog_unavailable", decision.reason)

    def test_build_app_from_json_configs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / "local.json"
            env_payload = {
                "runs_root": temp_dir,
                "dry_run": True,
                "button_calibration": str(CONFIGS_ROOT / "ui" / "button-calibration.json"),
            }
            env_path.write_text(json.dumps(env_payload, ensure_ascii=False), encoding="utf-8")

            app = build_app(
                BootstrapPaths(
                    env_config=env_path,
                    account_config=CONFIGS_ROOT / "accounts" / "instance-1.json",
                    scenario_config=CONFIGS_ROOT / "scenarios" / "battle-smoke.json",
                ),
                window_session=WindowSession(handle=1001, gateway=FakeWindowGateway()),
                input_gateway=NoOpInputGateway(),
            )

            result = app.run_once()

            self.assertEqual("instance-1", app.context.instance_id)
            self.assertEqual(1, len(result.executed_actions))
            self.assertTrue(result.observation.battle_ui_visible)
            self.assertTrue(result.observation.action_prompt_visible)
            self.assertEqual("CLICK_UI_BUTTON", result.executed_actions[0].action_type)
            self.assertIsNotNone(app.character_profile)
            self.assertEqual("mage-default", app.character_profile.character_id)
            self.assertIn("character_profile", app.context.metadata)
            self.assertEqual("mage-default", app.context.metadata["character_profile"]["character_id"])
            self.assertTrue(app.context.battle_session_id.startswith("battle-smoke"))

    def test_build_app_supports_round_script_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / "local.json"
            env_payload = {
                "runs_root": temp_dir,
                "dry_run": True,
                "button_calibration": str(CONFIGS_ROOT / "ui" / "button-calibration.json"),
            }
            env_path.write_text(json.dumps(env_payload, ensure_ascii=False), encoding="utf-8")

            app = build_app(
                BootstrapPaths(
                    env_config=env_path,
                    account_config=CONFIGS_ROOT / "accounts" / "instance-1.json",
                    scenario_config=CONFIGS_ROOT / "scenarios" / "battle-basic-validation.json",
                ),
                window_session=WindowSession(handle=1001, gateway=FakeWindowGateway()),
                input_gateway=NoOpInputGateway(),
            )

            result = app.run_once()

            self.assertEqual(2, len(result.executed_actions))
            self.assertEqual(["CLICK_UI_BUTTON", "CLICK_UI_BUTTON"], [item.action_type for item in result.executed_actions])
            self.assertTrue(app.context.battle_session_id.startswith("battle-basic-validation"))

    def test_build_app_rejects_character_config_outside_allowed_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            configs_root = root / "configs"
            account_config = configs_root / "accounts" / "instance-1.json"
            scenario_config = configs_root / "scenarios" / "battle-smoke.json"
            env_config = root / "env.json"
            outside_character = root / "outside-character.json"

            account_config.parent.mkdir(parents=True, exist_ok=True)
            scenario_config.parent.mkdir(parents=True, exist_ok=True)

            env_config.write_text(
                json.dumps(
                    {
                        "runs_root": str(root / "runs"),
                        "dry_run": True,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            scenario_config.write_text(
                json.dumps(
                    {
                        "scenario_id": "battle-smoke",
                        "initial_state": "ROUND_ACTIONABLE",
                        "primary_rule": {
                            "action_type": "CLICK_UI_BUTTON",
                            "reason": "test",
                            "parameters": {
                                "button_ref": "nonbattle_toolbar.bag_panel",
                            },
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            account_config.write_text(
                json.dumps(
                    {
                        "instance_id": "instance-1",
                        "character_config": "../../outside-character.json",
                        "enabled": True,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            outside_character.write_text(
                json.dumps(
                    {
                        "character_id": "outside",
                        "role_type": "mage",
                        "skill_set": [],
                        "default_target_rule": "enemy_front",
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                build_app(
                    BootstrapPaths(
                        env_config=env_config,
                        account_config=account_config,
                        scenario_config=scenario_config,
                    ),
                    window_session=WindowSession(handle=1001, gateway=FakeWindowGateway()),
                    input_gateway=NoOpInputGateway(),
                )


if __name__ == "__main__":
    unittest.main()
