from __future__ import annotations

import json
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from src.app import BootstrapPaths, JsonConfigLoader, build_app_from_configs
from src.app.service import AppTickResult
from src.app.window_binding import resolve_window_session
from src.domain import BattleState
from src.executor import Win32SendInputGateway
from src.platform import PyWin32WindowGateway

from .formatters import _slug, _utc_stamp
from .models import AutoBattleTickReport, ButtonCalibrationEntry, ManualProbeArtifacts


class ManualCoordinateProbeService:
    def __init__(self, project_root: Path) -> None:
        self._project_root = Path(project_root)
        self._gateway = PyWin32WindowGateway()
        self._input_gateway = Win32SendInputGateway()

    def run_probe(
        self,
        client_x: int,
        client_y: int,
        label: str,
        button_ref: str,
        delay_seconds: float,
    ) -> ManualProbeArtifacts:
        session = resolve_window_session(
            self._project_root / "configs" / "accounts" / "instance-1.json",
            gateway=self._gateway,
        )
        session.focus()
        time.sleep(0.15)

        info = session.snapshot()
        before = session.capture_client()
        screen_x = info.client_rect.left + int(client_x)
        screen_y = info.client_rect.top + int(client_y)
        self._input_gateway.click_screen(screen_x, screen_y)
        time.sleep(max(0.0, float(delay_seconds)))
        after = session.capture_client()

        probe_dir = self._project_root / "runs" / "artifacts" / "probes" / "manual-coordinate-ui"
        probe_dir.mkdir(parents=True, exist_ok=True)
        run_id = _utc_stamp()
        safe_label = _slug(label or "manual-probe")
        before_path = probe_dir / f"{run_id}-{safe_label}-before.png"
        after_path = probe_dir / f"{run_id}-{safe_label}-after.png"
        before.image.save(before_path)
        after.image.save(after_path)

        artifacts = ManualProbeArtifacts(
            run_id=run_id,
            handle=info.handle,
            client_x=int(client_x),
            client_y=int(client_y),
            screen_x=screen_x,
            screen_y=screen_y,
            before_path=str(before_path),
            after_path=str(after_path),
            before_hash=before.frame_hash,
            after_hash=after.frame_hash,
            frame_changed=before.frame_hash != after.frame_hash,
            delay_seconds=float(delay_seconds),
            label=label,
            button_ref=button_ref,
        )
        self._write_record(artifacts)
        return artifacts

    def save_feedback(self, run_id: str, status: str, notes: str) -> Path:
        record_path = self.record_path_for(run_id)
        payload = json.loads(record_path.read_text(encoding="utf-8-sig"))
        payload["status"] = status
        payload["notes"] = notes
        payload["reviewed_at"] = _utc_stamp()
        record_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return record_path

    def record_path_for(self, run_id: str) -> Path:
        return self._project_root / "runs" / "artifacts" / "probes" / "manual-coordinate-ui" / f"{run_id}.json"

    def _write_record(self, artifacts: ManualProbeArtifacts) -> Path:
        record_path = self.record_path_for(artifacts.run_id)
        record_path.write_text(json.dumps(asdict(artifacts), ensure_ascii=False, indent=2), encoding="utf-8")
        return record_path


class ButtonCalibrationStore:
    def __init__(self, project_root: Path) -> None:
        self._path = Path(project_root) / "configs" / "ui" / "button-calibration.json"

    @property
    def path(self) -> Path:
        return self._path

    def load_entries(self) -> list[ButtonCalibrationEntry]:
        payload = json.loads(self._path.read_text(encoding="utf-8-sig"))
        entries: list[ButtonCalibrationEntry] = []
        for group_name, group_payload in payload.items():
            if group_name == "version":
                continue
            for button_name, button_payload in group_payload.get("buttons", {}).items():
                point = button_payload.get("point", [0, 0])
                entries.append(
                    ButtonCalibrationEntry(
                        group=group_name,
                        name=button_name,
                        button_ref=f"{group_name}.{button_name}",
                        label=str(button_payload.get("label", button_name)),
                        x=int(point[0]),
                        y=int(point[1]),
                        status=str(button_payload.get("status", "unknown")),
                        notes=str(button_payload.get("notes", "")),
                    )
                )
        entries.sort(key=lambda item: (item.category, item.group, item.y, item.x, item.label))
        return entries

    def load_entry(self, button_ref: str) -> ButtonCalibrationEntry:
        for entry in self.load_entries():
            if entry.button_ref == button_ref:
                return entry
        raise KeyError(f"unknown button_ref={button_ref}")

    def update_entry(
        self,
        button_ref: str,
        *,
        x: int,
        y: int,
        status: str,
        label: str | None = None,
    ) -> ButtonCalibrationEntry:
        payload = json.loads(self._path.read_text(encoding="utf-8-sig"))
        group_name, button_name = button_ref.split(".", 1)
        try:
            button_payload = payload[group_name]["buttons"][button_name]
        except KeyError as exc:
            raise KeyError(f"unknown button_ref={button_ref}") from exc

        button_payload["point"] = [int(x), int(y)]
        button_payload["status"] = str(status)
        if label is not None:
            cleaned_label = label.strip()
            if cleaned_label:
                button_payload["label"] = cleaned_label

        self._path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return self.load_entry(button_ref)


class AutoBattleService:
    def __init__(self, project_root: Path) -> None:
        self._project_root = Path(project_root)
        self._loader = JsonConfigLoader()
        self._runtime_env_path: Path | None = None
        self._app = None
        self._ticks_run = 0

    @property
    def is_running(self) -> bool:
        return self._app is not None

    def start(self) -> tuple[str, str]:
        if self._app is not None:
            return self._session_root(), self._runtime_log_path()

        env_path = self._project_root / "configs" / "env" / "local.json"
        account_path = self._project_root / "configs" / "accounts" / "instance-1.json"
        scenario_path = self._project_root / "configs" / "scenarios" / "battle-basic-validation.json"

        env_config = self._loader.load(env_path)
        env_config["dry_run"] = False

        temp_env = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
        temp_env.write(json.dumps(env_config, ensure_ascii=False, indent=2))
        temp_env.flush()
        temp_env.close()
        self._runtime_env_path = Path(temp_env.name)

        self._app = build_app_from_configs(
            BootstrapPaths(
                env_config=self._runtime_env_path,
                account_config=account_path,
                scenario_config=scenario_path,
            ),
            input_gateway=Win32SendInputGateway(),
            gateway=PyWin32WindowGateway(),
        )
        self._app.window_session.focus()
        self._ticks_run = 0
        return self._session_root(), self._runtime_log_path()

    def stop(self) -> None:
        self._app = None
        self._ticks_run = 0
        if self._runtime_env_path is not None:
            self._runtime_env_path.unlink(missing_ok=True)
            self._runtime_env_path = None

    def run_tick(self) -> AutoBattleTickReport:
        if self._app is None:
            raise RuntimeError("auto battle app is not started")

        result: AppTickResult = self._app.run_once()
        self._ticks_run += 1
        return AutoBattleTickReport(
            tick_index=self._ticks_run,
            state=self._app.context.state.value,
            round_index=self._app.context.round_index,
            feedback_reason=str(self._app.context.metadata.get("last_action_feedback", "")),
            session_root=self._session_root(),
            runtime_log_path=self._runtime_log_path(),
            observation=result.observation,
            feedback_observation=result.feedback_observation,
            transitions=result.transitions,
            executed_actions=result.executed_actions,
            planned_actions=result.planned_actions,
            finished=self._app.context.state == BattleState.OUT_OF_BATTLE,
        )

    def _session_root(self) -> str:
        assert self._app is not None
        return str(self._app._runtime_session.artifacts.session_paths.root)

    def _runtime_log_path(self) -> str:
        assert self._app is not None
        return str(self._app._runtime_session.artifacts.session_paths.logs / "runtime.log")
