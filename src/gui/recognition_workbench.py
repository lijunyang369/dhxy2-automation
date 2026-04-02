from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import numpy as np

from src.app.bootstrap import BootstrapPaths, build_observation_pipeline
from src.app.observation_provider import DefaultObservationProvider
from src.app.window_binding import resolve_window_session
from src.perception.services import build_round_digit_template, refresh_round_digit_template_cache
from src.perception import RecognitionModuleResult, RecognitionModuleSpec, TemplateCatalog
from src.platform import PyWin32WindowGateway
from PIL import Image


def _utc_stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S%fZ")


@dataclass(frozen=True)
class RecognitionWorkbenchArtifacts:
    run_id: str
    screenshot_path: str
    record_path: str
    frame_hash: str
    module_results: tuple[RecognitionModuleResult, ...]
    region_crop_paths: dict[str, str]
    template_paths_by_module: dict[str, tuple[str, ...]]


class RecognitionWorkbenchService:
    def __init__(self, project_root: Path) -> None:
        self._project_root = Path(project_root)
        self._gateway = PyWin32WindowGateway()
        self._paths = BootstrapPaths(
            env_config=self._project_root / "configs" / "env" / "local.json",
            account_config=self._project_root / "configs" / "accounts" / "instance-1.json",
            scenario_config=self._project_root / "configs" / "scenarios" / "battle-basic-validation.json",
        )

    def module_specs(self) -> tuple[RecognitionModuleSpec, ...]:
        pipeline = build_observation_pipeline(self._paths, force_live=True)
        return pipeline.builder.module_specs

    @property
    def scenario_config_path(self) -> Path:
        return self._paths.scenario_config

    def region_rects(self) -> dict[str, tuple[int, int, int, int]]:
        payload = json.loads(self._paths.scenario_config.read_text(encoding="utf-8-sig"))
        rects: dict[str, tuple[int, int, int, int]] = {}
        for entry in payload.get("regions", []):
            raw = entry.get("rect")
            if not raw or len(raw) != 4:
                continue
            rects[str(entry["name"])] = tuple(int(value) for value in raw)
        return rects

    def update_region_rect(self, region_name: str, rect: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        payload = json.loads(self._paths.scenario_config.read_text(encoding="utf-8-sig"))
        updated_rect = tuple(int(value) for value in rect)
        found = False
        for entry in payload.get("regions", []):
            if str(entry.get("name")) != region_name:
                continue
            entry["rect"] = list(updated_rect)
            found = True
            break
        if not found:
            raise KeyError(f"unknown region_name={region_name}")
        self._paths.scenario_config.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return updated_rect

    def save_round_digit_template(self, digit: str, crop_path: str) -> Path:
        cleaned = digit.strip()
        if cleaned not in {str(index) for index in range(10)}:
            raise ValueError("round digit must be a single number between 0 and 9")
        source_path = Path(crop_path)
        if not source_path.is_file():
            raise FileNotFoundError(f"missing crop image: {source_path}")

        template = build_round_digit_template(Image.open(source_path))
        if template is None:
            raise ValueError("could not isolate round digit from crop")

        output_path = self._project_root / "resources" / "templates" / "battle" / f"battle_round_digit_{cleaned}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(template).save(output_path)
        refresh_round_digit_template_cache()
        return output_path

    def template_paths_by_module(self) -> dict[str, tuple[str, ...]]:
        env_payload = json.loads(self._paths.env_config.read_text(encoding="utf-8-sig"))
        template_catalog_path = env_payload.get("template_catalog")
        if not template_catalog_path:
            return {}
        catalog = TemplateCatalog.load(Path(template_catalog_path))
        by_template_id = {template.id: str(template.file) for template in catalog.all()}
        module_paths: dict[str, tuple[str, ...]] = {}
        for spec in self.module_specs():
            template_ids = _module_template_ids(spec)
            if spec.module_id == "battle_round":
                module_paths[spec.module_id] = self.round_digit_template_paths()
                continue
            if not template_ids:
                module_paths[spec.module_id] = ()
                continue
            module_paths[spec.module_id] = tuple(
                by_template_id[template_id]
                for template_id in template_ids
                if template_id in by_template_id
            )
        return module_paths

    def round_digit_template_paths(self) -> tuple[str, ...]:
        template_dir = self._project_root / "resources" / "templates" / "battle"
        return tuple(
            str(path)
            for path in sorted(template_dir.glob("battle_round_digit_*.png"))
        )

    def run(self) -> RecognitionWorkbenchArtifacts:
        pipeline = build_observation_pipeline(self._paths, force_live=True)
        provider = DefaultObservationProvider(
            template_matcher=pipeline.template_matcher,
            builder=pipeline.builder,
            config=pipeline.config,
        )
        session = resolve_window_session(self._paths.account_config, gateway=self._gateway)
        session.focus()
        time.sleep(0.15)
        capture = provider.capture(session)
        results_by_id = pipeline.builder.evaluate_snapshot(capture.snapshot)
        ordered_results = tuple(
            results_by_id[spec.module_id]
            for spec in pipeline.builder.module_specs
            if spec.module_id in results_by_id
        )
        template_paths_by_module = self.template_paths_by_module()

        run_id = _utc_stamp()
        run_dir = self._project_root / "runs" / "artifacts" / "probes" / "recognition-workbench" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = run_dir / "full.png"
        capture.frame.image.save(screenshot_path)

        region_crop_paths: dict[str, str] = {}
        for region_name, rect in capture.named_regions.items():
            crop_path = run_dir / f"region-{region_name}.png"
            capture.frame.image.crop(rect.as_bbox()).save(crop_path)
            region_crop_paths[region_name] = str(crop_path)

        record_path = run_dir / "result.json"
        record_path.write_text(
            json.dumps(
                _json_safe(
                    {
                        "run_id": run_id,
                        "screenshot_path": str(screenshot_path),
                        "frame_hash": capture.frame.frame_hash,
                        "region_crop_paths": region_crop_paths,
                        "template_paths_by_module": template_paths_by_module,
                        "module_results": [asdict(result) for result in ordered_results],
                    }
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return RecognitionWorkbenchArtifacts(
            run_id=run_id,
            screenshot_path=str(screenshot_path),
            record_path=str(record_path),
            frame_hash=capture.frame.frame_hash,
            module_results=ordered_results,
            region_crop_paths=region_crop_paths,
            template_paths_by_module=template_paths_by_module,
        )


def _json_safe(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _module_template_ids(spec: RecognitionModuleSpec) -> tuple[str, ...]:
    mapping = {
        "battle_scene": ("battle_ui",),
        "battle_action_prompt": ("battle_action_prompt",),
        "battle_skill_bar": ("battle_skill_bar",),
        "battle_target_select": ("battle_target_panel",),
        "battle_settlement": ("battle_settlement",),
    }
    return mapping.get(spec.module_id, ())
