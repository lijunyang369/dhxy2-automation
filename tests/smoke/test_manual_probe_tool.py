from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from src.app.recognition_workbench import RecognitionWorkbenchService
from src.app.manual_probe_tool import (
    AutoBattleTickReport,
    ButtonCalibrationStore,
    ManualCoordinateProbeService,
    ManualProbeArtifacts,
    format_auto_battle_tick_lines,
)
from src.domain import ActionType, AutomationAction, BattleObservation, BattleState, MatchResult, TransitionResult
from src.executor import ExecutionResult, ExecutionStep, StepType
from src.gui.recognition_workbench import _json_safe
from src.gui.manual_probe_tool import _snapshot_file_mtimes
from tests.smoke._paths import RUNS_ROOT


class ManualCoordinateProbeServiceTestCase(unittest.TestCase):
    def test_save_feedback_updates_existing_probe_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            record_dir = root / "runs" / "artifacts" / "probes" / "manual-coordinate-ui"
            record_dir.mkdir(parents=True, exist_ok=True)
            service = ManualCoordinateProbeService(root)
            record = ManualProbeArtifacts(
                run_id="test-run",
                handle=1,
                client_x=100,
                client_y=200,
                screen_x=300,
                screen_y=400,
                before_path="before.png",
                after_path="after.png",
                before_hash="before",
                after_hash="after",
                frame_changed=True,
                delay_seconds=0.8,
                label="manual-probe",
                button_ref="nonbattle_toolbar.bag_panel",
            )
            record_path = record_dir / "test-run.json"
            record_path.write_text(json.dumps(record.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")

            saved_path = service.save_feedback("test-run", "confirmed", "opened panel")
            payload = json.loads(saved_path.read_text(encoding="utf-8-sig"))

            self.assertEqual(record_path, saved_path)
            self.assertEqual("confirmed", payload["status"])
            self.assertEqual("opened panel", payload["notes"])
            self.assertIn("reviewed_at", payload)


class ButtonCalibrationStoreTestCase(unittest.TestCase):
    def test_load_entries_splits_character_pet_and_nonbattle_buttons(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / "configs" / "ui"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "button-calibration.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nonbattle_toolbar": {
                            "buttons": {
                                "bag_panel": {
                                    "label": "道具",
                                    "status": "confirmed",
                                    "point": [950, 792],
                                }
                            }
                        },
                        "battle_command_bar": {
                            "buttons": {
                                "defend": {
                                    "label": "防御",
                                    "status": "candidate",
                                    "point": [1252, 348],
                                }
                            }
                        },
                        "pet_battle_command_bar": {
                            "buttons": {
                                "spell": {
                                    "label": "法术",
                                    "status": "candidate",
                                    "point": [1247, 267],
                                }
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            store = ButtonCalibrationStore(root)
            entries = store.load_entries()

            self.assertEqual(3, len(entries))
            self.assertEqual("nonbattle", store.load_entry("nonbattle_toolbar.bag_panel").category)
            self.assertEqual("character_battle", store.load_entry("battle_command_bar.defend").category)
            self.assertEqual("pet_battle", store.load_entry("pet_battle_command_bar.spell").category)

    def test_update_entry_writes_new_point_and_status_back_to_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_dir = root / "configs" / "ui"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "button-calibration.json"
            config_path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "nonbattle_toolbar": {
                            "buttons": {
                                "friend_panel": {
                                    "label": "好友",
                                    "status": "candidate",
                                    "point": [1270, 792],
                                }
                            }
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            store = ButtonCalibrationStore(root)
            updated = store.update_entry(
                "nonbattle_toolbar.friend_panel",
                x=1282,
                y=805,
                status="confirmed",
                label="好友",
            )
            payload = json.loads(config_path.read_text(encoding="utf-8-sig"))

            self.assertEqual(1282, updated.x)
            self.assertEqual(805, updated.y)
            self.assertEqual("confirmed", updated.status)
            self.assertEqual([1282, 805], payload["nonbattle_toolbar"]["buttons"]["friend_panel"]["point"])
            self.assertEqual("confirmed", payload["nonbattle_toolbar"]["buttons"]["friend_panel"]["status"])


class AutoBattleLogFormattingTestCase(unittest.TestCase):
    def test_format_auto_battle_tick_lines_includes_recognition_action_and_result_sections(self) -> None:
        report = AutoBattleTickReport(
            tick_index=2,
            state="ROUND_WAITING",
            round_index=1,
            feedback_reason="action_feedback_confirmed",
            session_root="D:/runs/session",
            runtime_log_path="D:/runs/session/logs/runtime.log",
            observation=BattleObservation(
                battle_ui_visible=True,
                action_prompt_visible=False,
                skill_panel_visible=True,
                target_select_visible=False,
                settlement_visible=False,
                window_alive=True,
                window_focused=True,
                frame_timestamp=datetime.now(timezone.utc),
                frame_hash="frame-2",
                confidence_summary=0.97,
                matches=(
                    MatchResult(
                        template_id="battle_ui",
                        confidence=0.99,
                        region_name="battle_scene",
                    ),
                ),
                round_indicator_visible=True,
                round_number=4,
                round_digits=("4",),
                round_recognition_reason="test",
                round_recognition_confidence=0.96,
            ),
            feedback_observation=BattleObservation(
                battle_ui_visible=True,
                action_prompt_visible=False,
                skill_panel_visible=True,
                target_select_visible=False,
                settlement_visible=False,
                window_alive=True,
                window_focused=True,
                frame_timestamp=datetime.now(timezone.utc),
                frame_hash="frame-2-after",
                confidence_summary=0.97,
            ),
            transitions=(
                TransitionResult(
                    from_state=BattleState.ROUND_ACTIONABLE,
                    to_state=BattleState.ACTION_EXECUTING,
                    changed=True,
                    reason="plan_started",
                    observed_state=BattleState.ROUND_ACTIONABLE,
                ),
            ),
            planned_actions=(
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "battle_command_bar.escape"},
                ),
                AutomationAction(
                    action_type=ActionType.CLICK_UI_BUTTON,
                    parameters={"button_ref": "pet_battle_command_bar.defend"},
                ),
            ),
            executed_actions=(
                ExecutionResult(
                    action_type="CLICK_UI_BUTTON",
                    success=True,
                    steps=(
                        ExecutionStep(step_type=StepType.FOCUS_WINDOW),
                        ExecutionStep(step_type=StepType.CLICK, payload={"point": (1300, 455)}),
                    ),
                    message="action executed",
                ),
            ),
            finished=False,
        )

        lines = format_auto_battle_tick_lines(report)
        joined = "\n".join(lines)

        self.assertIn("当前场景：战斗场景", joined)
        self.assertIn("战斗识别：回合数=4", joined)
        self.assertIn("战斗回合：第 4 回合", joined)
        self.assertIn("人物指令：逃跑", joined)
        self.assertIn("宠物指令：防御", joined)


class HotReloadHelperTestCase(unittest.TestCase):
    def test_snapshot_file_mtimes_only_includes_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "exists.txt"
            missing = root / "missing.txt"
            existing.write_text("ok", encoding="utf-8")

            snapshot = _snapshot_file_mtimes((existing, missing))

            self.assertIn(str(existing), snapshot)
            self.assertNotIn(str(missing), snapshot)


class RecognitionWorkbenchServiceTestCase(unittest.TestCase):
    def test_update_region_rect_writes_back_to_scenario_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "configs" / "env").mkdir(parents=True, exist_ok=True)
            (root / "configs" / "accounts").mkdir(parents=True, exist_ok=True)
            (root / "configs" / "scenarios").mkdir(parents=True, exist_ok=True)
            (root / "resources" / "templates" / "battle").mkdir(parents=True, exist_ok=True)

            (root / "configs" / "env" / "local.json").write_text(
                json.dumps(
                    {
                        "template_catalog": str(root / "resources" / "templates" / "battle" / "catalog.json"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (root / "resources" / "templates" / "battle" / "catalog.json").write_text(
                json.dumps({"templates": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (root / "configs" / "accounts" / "instance-1.json").write_text(
                json.dumps({"instance_id": "instance-1"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            scenario_path = root / "configs" / "scenarios" / "battle-basic-validation.json"
            scenario_path.write_text(
                json.dumps(
                    {
                        "scenario_id": "battle-basic-validation",
                        "regions": [
                            {"name": "round_number_region", "rect": [0, 0, 180, 120]},
                            {"name": "battle_auto_button", "rect": [1290, 700, 1368, 750], "use_template_match": True},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            service = RecognitionWorkbenchService(root)
            updated = service.update_region_rect("round_number_region", (1, 2, 300, 160))
            payload = json.loads(scenario_path.read_text(encoding="utf-8-sig"))

            self.assertEqual((1, 2, 300, 160), updated)
            self.assertEqual([1, 2, 300, 160], payload["regions"][0]["rect"])
            self.assertEqual((1, 2, 300, 160), service.region_rects()["round_number_region"])

    def test_save_round_digit_template_writes_real_digit_template_and_updates_module_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "configs" / "env").mkdir(parents=True, exist_ok=True)
            (root / "configs" / "accounts").mkdir(parents=True, exist_ok=True)
            (root / "configs" / "scenarios").mkdir(parents=True, exist_ok=True)
            (root / "resources" / "templates" / "battle").mkdir(parents=True, exist_ok=True)

            (root / "configs" / "env" / "local.json").write_text(
                json.dumps(
                    {
                        "template_catalog": str(root / "resources" / "templates" / "battle" / "catalog.json"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            (root / "resources" / "templates" / "battle" / "catalog.json").write_text(
                json.dumps({"templates": []}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (root / "configs" / "accounts" / "instance-1.json").write_text(
                json.dumps({"instance_id": "instance-1"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (root / "configs" / "scenarios" / "battle-basic-validation.json").write_text(
                json.dumps(
                    {
                        "scenario_id": "battle-basic-validation",
                        "regions": [
                            {"name": "round_number_region", "rect": [0, 0, 180, 120]},
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            service = RecognitionWorkbenchService(root)
            crop_path = (
                RUNS_ROOT
                / "artifacts"
                / "probes"
                / "recognition-workbench"
                / "20260401T092306780541Z"
                / "region-battle_main.png"
            )

            output_path = service.save_round_digit_template("3", str(crop_path))
            module_paths = service.template_paths_by_module()

            self.assertTrue(output_path.is_file())
            self.assertIn(str(output_path), module_paths["battle_round"])


class RecognitionWorkbenchJsonSafeTestCase(unittest.TestCase):
    def test_json_safe_converts_numpy_scalars(self) -> None:
        payload = {
            "int": np.int32(4),
            "float": np.float32(0.75),
            "nested": [{"value": np.int64(9)}],
        }

        safe = _json_safe(payload)
        encoded = json.dumps(safe, ensure_ascii=False)

        self.assertEqual(4, safe["int"])
        self.assertAlmostEqual(0.75, safe["float"], places=5)
        self.assertEqual(9, safe["nested"][0]["value"])
        self.assertIn('"int": 4', encoded)


if __name__ == "__main__":
    unittest.main()
