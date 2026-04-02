from __future__ import annotations

import json
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk

from PIL import Image, ImageTk

from src.gui.recognition_workbench import RecognitionWorkbenchArtifacts, RecognitionWorkbenchService
from src.gui.theme import configure_workbench_theme
from src.gui.formatters import (
    _feedback_label,
    _planned_command_summary,
    _recognition_status_label,
    _scene_label,
    _snapshot_file_mtimes,
    format_auto_battle_tick_lines,
)
from src.gui.models import AutoBattleTickReport, ButtonCalibrationEntry, ManualProbeArtifacts
from src.gui.pages import BasePageController, build_page_controllers
from src.gui.services import AutoBattleService, ButtonCalibrationStore, ManualCoordinateProbeService
from src.perception import RecognitionModuleSpec


class ManualCoordinateProbeApp:
    STATUS_OPTIONS = ("confirmed", "candidate", "pending", "uncertain", "missed", "blocked")

    def __init__(
        self,
        root: tk.Tk,
        probe_service: ManualCoordinateProbeService,
        calibration_store: ButtonCalibrationStore,
        auto_battle_service: AutoBattleService,
        recognition_workbench_service: RecognitionWorkbenchService,
    ) -> None:
        self._root = root
        self._probe_service = probe_service
        self._calibration_store = calibration_store
        self._auto_battle_service = auto_battle_service
        self._recognition_workbench_service = recognition_workbench_service
        self._last_run_id = ""
        self._selected_button_ref = ""
        self._selected_recognition_module_id = ""
        self._auto_tick_job: str | None = None
        self._hot_reload_job: str | None = None
        self._last_battle_scene = ""
        self._last_battle_round_logged = 0
        self._project_root = Path(os.environ.get("DHXY_TOOL_PROJECT_ROOT", self._calibration_store.path.parents[2]))
        self._launcher_path = Path(os.environ["DHXY_TOOL_LAUNCHER"]) if os.environ.get("DHXY_TOOL_LAUNCHER") else None

        self._entries_by_ref: dict[str, ButtonCalibrationEntry] = {}
        self._refs_by_category: dict[str, list[str]] = {
            "character_battle": [],
            "pet_battle": [],
            "nonbattle": [],
        }
        self._listboxes: dict[str, tk.Listbox] = {}
        self._pages: dict[str, ttk.Frame] = {}
        self._page_controllers: dict[str, BasePageController] = {}
        self._recognition_module_specs: tuple[RecognitionModuleSpec, ...] = (
            self._recognition_workbench_service.module_specs()
        )
        self._recognition_template_paths_by_module: dict[str, tuple[str, ...]] = (
            self._recognition_workbench_service.template_paths_by_module()
        )
        self._recognition_results_by_id: dict[str, RecognitionModuleResult] = {}
        self._recognition_artifacts: RecognitionWorkbenchArtifacts | None = None

        self._button_ref_var = tk.StringVar(value="")
        self._button_name_var = tk.StringVar(value="")
        self._x_var = tk.StringVar(value="")
        self._y_var = tk.StringVar(value="")
        self._label_var = tk.StringVar(value="")
        self._delay_var = tk.StringVar(value="0.8")
        self._status_var = tk.StringVar(value="candidate")
        self._result_var = tk.StringVar(value="就绪")
        self._before_path_var = tk.StringVar(value="")
        self._after_path_var = tk.StringVar(value="")
        self._record_path_var = tk.StringVar(value="")
        self._config_path_var = tk.StringVar(value=str(self._calibration_store.path))
        self._summary_var = tk.StringVar(value="")

        self._auto_enabled_var = tk.BooleanVar(value=False)
        self._auto_status_var = tk.StringVar(value="空闲")
        self._auto_tick_var = tk.StringVar(value="0")
        self._auto_state_var = tk.StringVar(value="未开始")
        self._auto_feedback_var = tk.StringVar(value="")
        self._auto_session_var = tk.StringVar(value="")
        self._auto_runtime_log_var = tk.StringVar(value="")
        self._recognition_module_id_var = tk.StringVar(value="")
        self._recognition_region_var = tk.StringVar(value="")
        self._recognition_mode_var = tk.StringVar(value="")
        self._recognition_detected_var = tk.StringVar(value="")
        self._recognition_confidence_var = tk.StringVar(value="")
        self._recognition_summary_text_var = tk.StringVar(value="")
        self._recognition_left_var = tk.StringVar(value="")
        self._recognition_top_var = tk.StringVar(value="")
        self._recognition_right_var = tk.StringVar(value="")
        self._recognition_bottom_var = tk.StringVar(value="")
        self._recognition_config_path_var = tk.StringVar(
            value=str(self._recognition_workbench_service.scenario_config_path)
        )
        self._recognition_full_path_var = tk.StringVar(value="")
        self._recognition_crop_path_var = tk.StringVar(value="")
        self._recognition_template_path_var = tk.StringVar(value="")
        self._recognition_record_path_var = tk.StringVar(value="")
        self._recognition_round_digit_var = tk.StringVar(value="")
        self._recognition_round_template_status_var = tk.StringVar(value="")

        self._notes_widget: tk.Text | None = None
        self._home_log_widget: tk.Text | None = None
        self._battle_log_widget: tk.Text | None = None
        self._recognition_log_widget: tk.Text | None = None
        self._recognition_listbox: tk.Listbox | None = None
        self._before_preview_label: ttk.Label | None = None
        self._after_preview_label: ttk.Label | None = None
        self._recognition_full_preview_label: ttk.Label | None = None
        self._recognition_crop_preview_label: ttk.Label | None = None
        self._recognition_template_preview_label: ttk.Label | None = None
        self._before_preview_image: ImageTk.PhotoImage | None = None
        self._after_preview_image: ImageTk.PhotoImage | None = None
        self._recognition_full_preview_image: ImageTk.PhotoImage | None = None
        self._recognition_crop_preview_image: ImageTk.PhotoImage | None = None
        self._recognition_template_preview_image: ImageTk.PhotoImage | None = None

        configure_workbench_theme(self._root)
        self._root.title("大话西游2自动化运行平台")
        self._root.geometry("1360x860")
        self._root.minsize(1180, 760)

        self._hot_reload_source_paths = self._build_hot_reload_source_paths()
        self._hot_reload_config_paths = self._build_hot_reload_config_paths()
        self._hot_reload_mtimes = _snapshot_file_mtimes(self._hot_reload_source_paths + self._hot_reload_config_paths)

        self._build()
        self._append_home_log("INFO", f"tool_started config={self._calibration_store.path}")
        self._reload_entries()
        self._show_page("home")
        self._schedule_hot_reload_poll()
        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self) -> None:
        outer = ttk.Frame(self._root, padding=12)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(1, weight=1)
        ttk.Label(header, text="大话西游2自动化运行平台", style="Title.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(header, textvariable=self._summary_var, style="Muted.TLabel").grid(row=0, column=1, sticky="e")

        body = ttk.Frame(outer)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        self._page_controllers = build_page_controllers(self, body)
        self._pages = {name: controller.frame for name, controller in self._page_controllers.items()}

        for page in self._pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    def _build_hot_reload_source_paths(self) -> tuple[Path, ...]:
        paths: list[Path] = []
        for relative in (
            "src/gui/manual_probe_tool.py",
            "src/gui/pages.py",
            "src/gui/services.py",
            "src/gui/models.py",
            "src/gui/formatters.py",
            "src/gui/theme.py",
            "src/gui/recognition_workbench.py",
            "src/app/bootstrap.py",
            "src/app/observation_provider.py",
            "src/app/service.py",
            "src/app/action_feedback.py",
            "src/perception/observation.py",
            "src/perception/battle_recognizers.py",
            "src/perception/recognizer_models.py",
            "src/perception/services.py",
            "src/policy/planner.py",
            "src/state_machine/machine.py",
            "src/state_machine/guards.py",
            "src/state_machine/resolver.py",
        ):
            candidate = self._project_root / relative
            if candidate.is_file():
                paths.append(candidate)
        if self._launcher_path is not None and self._launcher_path.is_file():
            paths.append(self._launcher_path)
        return tuple(paths)

    def _build_hot_reload_config_paths(self) -> tuple[Path, ...]:
        paths: list[Path] = []
        for relative in (
            "configs/ui/button-calibration.json",
            "configs/ui/battle-button-semantics.json",
            "configs/scenarios/battle-basic-validation.json",
            "configs/accounts/instance-1.json",
            "configs/env/local.json",
        ):
            candidate = self._project_root / relative
            if candidate.is_file():
                paths.append(candidate)
        return tuple(paths)

    def _show_page(self, name: str) -> None:
        for page_name, frame in self._pages.items():
            if page_name == name:
                frame.tkraise()
        if name == "recognition" and self._recognition_module_specs and not self._selected_recognition_module_id:
            self._select_recognition_module_by_id(self._recognition_module_specs[0].module_id)
        self._append_home_log("INFO", f"open_page page={name}")

    def _populate_recognition_module_listbox(self) -> None:
        if self._recognition_listbox is None:
            return
        self._recognition_listbox.delete(0, tk.END)
        for spec in self._recognition_module_specs:
            result = self._recognition_results_by_id.get(spec.module_id)
            status = _recognition_status_label(result)
            self._recognition_listbox.insert(tk.END, f"[{status}] {spec.label}")

    def _on_select_recognition_module(self, _event: object | None = None) -> None:
        if self._recognition_listbox is None:
            return
        selected = self._recognition_listbox.curselection()
        if not selected:
            return
        spec = self._recognition_module_specs[selected[0]]
        self._selected_recognition_module_id = spec.module_id
        result = self._recognition_results_by_id.get(spec.module_id)
        self._load_recognition_module(spec, result)

    def _run_selected_recognition_capture(self) -> None:
        if not self._selected_recognition_module_id:
            self._append_home_log("WARN", "recognition_run_skipped no_selected_module")
            return
        self._run_recognition_capture(selected_module_id=self._selected_recognition_module_id)

    def _run_recognition_capture(self, selected_module_id: str | None = None) -> None:
        try:
            artifacts = self._recognition_workbench_service.run()
        except Exception as exc:
            self._append_home_log("ERROR", f"recognition_run_failed error={exc}")
            self._set_recognition_log_text(f"识别失败: {exc}")
            return

        self._recognition_artifacts = artifacts
        self._recognition_results_by_id = {
            result.module_id: result for result in artifacts.module_results
        }
        self._recognition_template_paths_by_module = dict(artifacts.template_paths_by_module)
        self._recognition_full_path_var.set(artifacts.screenshot_path)
        self._recognition_record_path_var.set(artifacts.record_path)
        self._populate_recognition_module_listbox()
        self._append_home_log("INFO", f"recognition_run_completed run={artifacts.run_id}")

        target_module_id = selected_module_id
        if not target_module_id or target_module_id not in self._recognition_results_by_id:
            if self._selected_recognition_module_id in self._recognition_results_by_id:
                target_module_id = self._selected_recognition_module_id
            elif artifacts.module_results:
                target_module_id = artifacts.module_results[0].module_id

        if not target_module_id:
            return
        self._select_recognition_module_by_id(target_module_id)

    def _select_recognition_module_by_id(self, module_id: str) -> None:
        if self._recognition_listbox is None:
            return
        for index, spec in enumerate(self._recognition_module_specs):
            if spec.module_id != module_id:
                continue
            self._recognition_listbox.selection_clear(0, tk.END)
            self._recognition_listbox.selection_set(index)
            self._recognition_listbox.activate(index)
            self._on_select_recognition_module()
            return

    def _load_recognition_module(
        self,
        spec: RecognitionModuleSpec,
        result: RecognitionModuleResult | None,
    ) -> None:
        self._recognition_module_id_var.set(spec.module_id)
        self._recognition_region_var.set(spec.region_name)
        self._recognition_mode_var.set(spec.mode)
        self._recognition_detected_var.set(_recognition_status_label(result))
        self._recognition_confidence_var.set("" if result is None else f"{result.confidence:.4f}")
        self._load_recognition_region_rect(spec.region_name)
        if spec.module_id != "battle_round":
            self._recognition_round_digit_var.set("")
        self._recognition_summary_text_var.set("尚未执行识别" if result is None else result.summary)

        screenshot_path = self._recognition_artifacts.screenshot_path if self._recognition_artifacts else ""
        crop_path = ""
        template_path = ""
        if self._recognition_artifacts is not None:
            crop_path = self._recognition_artifacts.region_crop_paths.get(spec.region_name, "")
            self._recognition_record_path_var.set(self._recognition_artifacts.record_path)
        template_paths = self._recognition_template_paths_by_module.get(spec.module_id, ())
        if template_paths:
            template_path = template_paths[0]
        self._recognition_full_path_var.set(screenshot_path)
        self._recognition_crop_path_var.set(crop_path)
        self._recognition_template_path_var.set(template_path)
        if spec.module_id != "battle_round":
            self._recognition_round_template_status_var.set("")
        self._update_recognition_previews(screenshot_path, crop_path, template_path)

        if result is None:
            details_text = "尚未执行识别。"
        else:
            details_text = json.dumps(result.details, ensure_ascii=False, indent=2)
        self._set_recognition_log_text(details_text)

    def _set_recognition_log_text(self, message: str) -> None:
        if self._recognition_log_widget is None:
            return
        self._recognition_log_widget.configure(state="normal")
        self._recognition_log_widget.delete("1.0", tk.END)
        self._recognition_log_widget.insert("1.0", message)
        self._recognition_log_widget.configure(state="disabled")

    def _load_recognition_region_rect(self, region_name: str) -> None:
        rect = self._recognition_workbench_service.region_rects().get(region_name)
        if rect is None:
            self._recognition_left_var.set("")
            self._recognition_top_var.set("")
            self._recognition_right_var.set("")
            self._recognition_bottom_var.set("")
            return
        left, top, right, bottom = rect
        self._recognition_left_var.set(str(left))
        self._recognition_top_var.set(str(top))
        self._recognition_right_var.set(str(right))
        self._recognition_bottom_var.set(str(bottom))

    def _save_recognition_region(self) -> None:
        if not self._selected_recognition_module_id:
            self._append_home_log("WARN", "save_recognition_region_skipped no_selected_module")
            return
        spec = next(
            (item for item in self._recognition_module_specs if item.module_id == self._selected_recognition_module_id),
            None,
        )
        if spec is None:
            self._append_home_log("WARN", "save_recognition_region_skipped module_missing")
            return
        try:
            rect = (
                int(self._recognition_left_var.get().strip()),
                int(self._recognition_top_var.get().strip()),
                int(self._recognition_right_var.get().strip()),
                int(self._recognition_bottom_var.get().strip()),
            )
            self._recognition_workbench_service.update_region_rect(spec.region_name, rect)
        except Exception as exc:
            self._append_home_log("ERROR", f"save_recognition_region_failed error={exc}")
            self._set_recognition_log_text(f"保存区域失败: {exc}")
            return

        self._append_home_log(
            "INFO",
            f"save_recognition_region module={spec.module_id} region={spec.region_name} rect={rect}",
        )
        self._load_recognition_region_rect(spec.region_name)

    def _save_round_digit_template(self) -> None:
        if self._selected_recognition_module_id != "battle_round":
            self._set_recognition_log_text("仅战斗回合识别模块支持保存数字模板。")
            return
        crop_path = self._recognition_crop_path_var.get().strip()
        digit = self._recognition_round_digit_var.get().strip()
        if not crop_path:
            self._set_recognition_log_text("请先执行一次战斗回合识别，生成当前裁图。")
            return
        try:
            template_path = self._recognition_workbench_service.save_round_digit_template(digit, crop_path)
        except Exception as exc:
            self._recognition_round_template_status_var.set(f"failed: {exc}")
            self._set_recognition_log_text(f"保存回合数字模板失败: {exc}")
            self._append_home_log("ERROR", f"save_round_digit_template_failed error={exc}")
            return

        self._recognition_template_paths_by_module = self._recognition_workbench_service.template_paths_by_module()
        self._recognition_template_path_var.set(str(template_path))
        self._recognition_round_template_status_var.set(f"saved digit={digit}")
        self._update_recognition_previews(
            self._recognition_full_path_var.get().strip(),
            crop_path,
            str(template_path),
        )
        self._append_home_log("INFO", f"save_round_digit_template digit={digit} path={template_path.name}")

    def _update_recognition_previews(self, screenshot_path: str, crop_path: str, template_path: str) -> None:
        self._recognition_full_preview_image = self._load_preview_image(screenshot_path)
        self._recognition_crop_preview_image = self._load_preview_image(crop_path)
        self._recognition_template_preview_image = self._load_preview_image(template_path)
        self._set_preview(self._recognition_full_preview_label, self._recognition_full_preview_image, screenshot_path)
        self._set_preview(self._recognition_crop_preview_label, self._recognition_crop_preview_image, crop_path)
        self._set_preview(
            self._recognition_template_preview_label,
            self._recognition_template_preview_image,
            template_path,
        )
        if not template_path and self._recognition_template_preview_label is not None:
            self._recognition_template_preview_label.configure(text="无模板")

    def _add_entry(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=(6, 0))

    def _add_readonly_entry(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(parent, textvariable=variable, state="readonly").grid(row=row, column=1, sticky="ew", pady=(6, 0))

    def _reload_entries(self) -> None:
        entries = self._calibration_store.load_entries()
        self._entries_by_ref = {entry.button_ref: entry for entry in entries}
        for category in self._refs_by_category:
            self._refs_by_category[category] = [entry.button_ref for entry in entries if entry.category == category]
        for category, listbox in self._listboxes.items():
            self._populate_listbox(listbox, self._refs_by_category[category])

        self._summary_var.set(
            "角色战斗 "
            f"{len(self._refs_by_category['character_battle'])} | "
            f"宠物战斗 {len(self._refs_by_category['pet_battle'])} | "
            f"非战斗 {len(self._refs_by_category['nonbattle'])}"
        )
        self._append_home_log(
            "INFO",
            "reload_calibration "
            f"character_battle={len(self._refs_by_category['character_battle'])} "
            f"pet_battle={len(self._refs_by_category['pet_battle'])} "
            f"nonbattle={len(self._refs_by_category['nonbattle'])}",
        )

        if self._selected_button_ref in self._entries_by_ref:
            self._load_entry(self._entries_by_ref[self._selected_button_ref])
        elif entries:
            self._load_entry(entries[0])

    def _populate_listbox(self, listbox: tk.Listbox, refs: list[str]) -> None:
        listbox.delete(0, tk.END)
        for button_ref in refs:
            entry = self._entries_by_ref[button_ref]
            listbox.insert(tk.END, f"[{entry.status:<9}] {entry.label} ({entry.x}, {entry.y})")

    def _on_select_entry(self, category: str) -> None:
        source_listbox = self._listboxes[category]
        selected = source_listbox.curselection()
        if not selected:
            return

        for other_category, listbox in self._listboxes.items():
            if other_category != category:
                listbox.selection_clear(0, tk.END)

        refs = self._refs_by_category[category]
        self._load_entry(self._entries_by_ref[refs[selected[0]]])

    def _load_entry(self, entry: ButtonCalibrationEntry) -> None:
        self._selected_button_ref = entry.button_ref
        self._button_ref_var.set(entry.button_ref)
        self._button_name_var.set(f"{entry.section_label} / {entry.name}")
        self._x_var.set(str(entry.x))
        self._y_var.set(str(entry.y))
        self._label_var.set(entry.label)
        self._status_var.set(entry.status)
        if self._notes_widget is not None:
            self._notes_widget.delete("1.0", tk.END)
            if entry.notes:
                self._notes_widget.insert("1.0", entry.notes)
        self._result_var.set(f"loaded {entry.button_ref}")
        self._append_home_log(
            "INFO",
            f"select_button ref={entry.button_ref} label={entry.label} point=({entry.x}, {entry.y}) status={entry.status}",
        )

    def _selected_notes(self) -> str:
        if self._notes_widget is None:
            return ""
        return self._notes_widget.get("1.0", tk.END).strip()

    def _save_calibration(self) -> None:
        if not self._selected_button_ref:
            self._result_var.set("未选择按钮")
            self._append_home_log("WARN", "save_calibration_skipped no_selected_button")
            return

        try:
            saved = self._calibration_store.update_entry(
                self._selected_button_ref,
                x=int(self._x_var.get().strip()),
                y=int(self._y_var.get().strip()),
                status=self._status_var.get().strip(),
                label=self._label_var.get().strip(),
            )
        except Exception as exc:
            self._result_var.set(f"保存校准失败: {exc}")
            self._append_home_log("ERROR", f"save_calibration_failed error={exc}")
            return

        self._reload_entries()
        self._load_entry(saved)
        self._result_var.set(f"saved {saved.button_ref} -> ({saved.x}, {saved.y}) status={saved.status}")
        self._append_home_log("INFO", f"save_calibration ref={saved.button_ref}")

    def _run_probe(self) -> None:
        try:
            artifacts = self._probe_service.run_probe(
                client_x=int(self._x_var.get().strip()),
                client_y=int(self._y_var.get().strip()),
                label=self._label_var.get().strip() or self._selected_button_ref or "manual-probe",
                button_ref=self._button_ref_var.get().strip(),
                delay_seconds=float(self._delay_var.get().strip() or "0.8"),
            )
        except Exception as exc:
            self._result_var.set(f"探针执行失败: {exc}")
            self._append_home_log("ERROR", f"probe_failed error={exc}")
            return

        self._last_run_id = artifacts.run_id
        self._before_path_var.set(artifacts.before_path)
        self._after_path_var.set(artifacts.after_path)
        self._record_path_var.set(str(self._probe_service.record_path_for(artifacts.run_id)))
        self._update_image_previews(artifacts.before_path, artifacts.after_path)
        self._result_var.set(
            f"run={artifacts.run_id} frame_changed={artifacts.frame_changed} "
            f"screen=({artifacts.screen_x}, {artifacts.screen_y})"
        )
        self._append_home_log(
            "INFO",
            f"probe_completed run={artifacts.run_id} before={Path(artifacts.before_path).name} after={Path(artifacts.after_path).name}",
        )

    def _save_feedback(self) -> None:
        if not self._last_run_id:
            self._result_var.set("没有可保存的探针记录")
            self._append_home_log("WARN", "save_feedback_skipped no_probe_record")
            return

        try:
            record_path = self._probe_service.save_feedback(
                run_id=self._last_run_id,
                status=self._status_var.get().strip(),
                notes=self._selected_notes(),
            )
        except Exception as exc:
            self._result_var.set(f"保存判定失败: {exc}")
            self._append_home_log("ERROR", f"save_feedback_failed error={exc}")
            return

        self._record_path_var.set(str(record_path))
        self._result_var.set(f"判定已保存：{record_path.name}")
        self._append_home_log("INFO", f"save_feedback run={self._last_run_id} status={self._status_var.get().strip()}")

    def _update_image_previews(self, before_path: str, after_path: str) -> None:
        self._before_preview_image = self._load_preview_image(before_path)
        self._after_preview_image = self._load_preview_image(after_path)
        self._set_preview(self._before_preview_label, self._before_preview_image, before_path)
        self._set_preview(self._after_preview_label, self._after_preview_image, after_path)

    def _load_preview_image(self, image_path: str) -> ImageTk.PhotoImage | None:
        path = Path(image_path)
        if not path.is_file():
            return None
        image = Image.open(path)
        image.thumbnail((320, 220))
        return ImageTk.PhotoImage(image)

    def _set_preview(
        self,
        label: ttk.Label | None,
        image: ImageTk.PhotoImage | None,
        image_path: str,
    ) -> None:
        if label is None:
            return
        if image is None:
            label.configure(image="", text="暂无图片")
            return
        label.configure(image=image, text=Path(image_path).name)

    def _start_auto_battle(self) -> None:
        if not self._auto_enabled_var.get():
            self._auto_status_var.set("已禁用")
            self._append_battle_log("自动战斗已关闭，请先勾选“开启自动战斗”。")
            self._append_home_log("WARN", "auto_battle_start_blocked disabled")
            return

        try:
            session_root, runtime_log = self._auto_battle_service.start()
        except Exception as exc:
            self._auto_status_var.set("启动失败")
            self._append_battle_log(f"启动失败：{exc}")
            self._append_home_log("ERROR", f"auto_battle_start_failed error={exc}")
            return

        self._auto_status_var.set("运行中")
        self._auto_session_var.set(session_root)
        self._auto_runtime_log_var.set(runtime_log)
        self._last_battle_scene = ""
        self._last_battle_round_logged = 0
        self._clear_battle_log()
        self._append_battle_log(f"自动战斗已启动，会话目录：{session_root}")
        self._append_home_log("INFO", f"auto_battle_started session={session_root}")
        self._schedule_next_tick(200)

    def _stop_auto_battle(self) -> None:
        if self._auto_tick_job is not None:
            self._root.after_cancel(self._auto_tick_job)
            self._auto_tick_job = None
        self._auto_battle_service.stop()
        self._auto_status_var.set("已停止")
        self._last_battle_scene = ""
        self._last_battle_round_logged = 0
        self._append_battle_log("自动战斗已停止")
        self._append_home_log("INFO", "auto_battle_stopped")

    def _schedule_next_tick(self, delay_ms: int) -> None:
        if self._auto_tick_job is not None:
            self._root.after_cancel(self._auto_tick_job)
        self._auto_tick_job = self._root.after(delay_ms, self._run_auto_battle_tick)

    def _run_auto_battle_tick(self) -> None:
        self._auto_tick_job = None
        if not self._auto_enabled_var.get():
            self._stop_auto_battle()
            return
        if not self._auto_battle_service.is_running:
            return

        try:
            report = self._auto_battle_service.run_tick()
        except Exception as exc:
            self._auto_status_var.set("轮询失败")
            self._append_battle_log(f"轮询失败：{exc}")
            self._append_home_log("ERROR", f"auto_battle_tick_failed error={exc}")
            self._auto_battle_service.stop()
            return

        self._auto_tick_var.set(str(report.tick_index))
        self._auto_state_var.set(_state_label(report.state))
        self._auto_feedback_var.set(_feedback_label(report.feedback_reason) if report.feedback_reason else "暂无")
        self._auto_session_var.set(report.session_root)
        self._auto_runtime_log_var.set(report.runtime_log_path)
        self._append_battle_report_clean(report)

        if report.finished:
            self._auto_status_var.set("已完成")
            self._append_home_log("INFO", f"auto_battle_finished tick={report.tick_index}")
            self._auto_battle_service.stop()
            return

        self._auto_status_var.set("运行中")
        self._schedule_next_tick(1200)

    def _append_battle_report(self, report: AutoBattleTickReport) -> None:
        scene = _scene_label(report.observation)
        if scene != self._last_battle_scene:
            self._append_battle_log(f"当前场景：{scene}")
            self._last_battle_scene = scene

        if not report.observation.battle_ui_visible:
            return

        if not report.executed_actions:
            return

        round_number = report.observation.round_number or max(1, report.round_index)
        if round_number != self._last_battle_round_logged:
            self._append_battle_log(f"识别到新回合：第 {round_number} 回合")
            self._last_battle_round_logged = round_number

        character_command, pet_command = _planned_command_summary(report.planned_actions)
        self._append_battle_log(f"新回合执行策略：人物={character_command}，宠物={pet_command}")
        self._append_battle_log(f"实际执行指令：人物={character_command}，宠物={pet_command}")
        self._append_battle_log(f"操作完成：{_feedback_label(report.feedback_reason)}")

    def _append_battle_report_clean(self, report: AutoBattleTickReport) -> None:
        scene_observation = report.feedback_observation if report.finished and report.feedback_observation is not None else report.observation
        scene = _scene_label(scene_observation)
        if scene != self._last_battle_scene:
            self._append_battle_log(f"当前场景：{scene}")
            self._last_battle_scene = scene

        if not report.executed_actions:
            return

        round_number = max(1, report.round_index)
        if round_number != self._last_battle_round_logged:
            self._append_battle_log(f"识别到新回合：第 {round_number} 回合")
            self._last_battle_round_logged = round_number

        character_command, pet_command = _planned_command_summary(report.planned_actions)
        self._append_battle_log(f"新回合执行策略：人物={character_command}，宠物={pet_command}")
        self._append_battle_log(f"实际执行指令：人物={character_command}，宠物={pet_command}")
        self._append_battle_log(f"操作完成：{_feedback_label(report.feedback_reason)}")

    def _clear_battle_log(self) -> None:
        if self._battle_log_widget is None:
            return
        self._battle_log_widget.configure(state="normal")
        self._battle_log_widget.delete("1.0", tk.END)
        self._battle_log_widget.configure(state="disabled")

    def _append_home_log(self, level: str, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {level}: {message}\n"
        if self._home_log_widget is None:
            return
        self._home_log_widget.configure(state="normal")
        self._home_log_widget.insert(tk.END, line)
        self._home_log_widget.see(tk.END)
        self._home_log_widget.configure(state="disabled")

    def _append_battle_log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}\n"
        if self._battle_log_widget is None:
            return
        self._battle_log_widget.configure(state="normal")
        self._battle_log_widget.insert(tk.END, line)
        self._battle_log_widget.see(tk.END)
        self._battle_log_widget.configure(state="disabled")

    def _schedule_hot_reload_poll(self, delay_ms: int = 1500) -> None:
        if self._hot_reload_job is not None:
            self._root.after_cancel(self._hot_reload_job)
        self._hot_reload_job = self._root.after(delay_ms, self._poll_hot_reload)

    def _poll_hot_reload(self) -> None:
        self._hot_reload_job = None
        current_snapshot = _snapshot_file_mtimes(self._hot_reload_source_paths + self._hot_reload_config_paths)

        changed_sources = [
            path for path in self._hot_reload_source_paths
            if self._hot_reload_mtimes.get(str(path)) != current_snapshot.get(str(path))
        ]
        if changed_sources:
            self._append_home_log("INFO", f"hot_reload_detected source={changed_sources[0].name}")
            self._restart_process_for_hot_reload()
            return

        changed_configs = [
            path for path in self._hot_reload_config_paths
            if self._hot_reload_mtimes.get(str(path)) != current_snapshot.get(str(path))
        ]
        if changed_configs:
            self._hot_reload_mtimes = current_snapshot
            self._reload_entries()
            self._append_home_log("INFO", f"hot_reload_applied config={changed_configs[0].name}")
            if self._auto_battle_service.is_running:
                self._append_battle_log("检测到配置变更：当前自动战斗继续运行，新配置将在下次启动时生效")
            self._schedule_hot_reload_poll()
            return

        self._hot_reload_mtimes = current_snapshot
        self._schedule_hot_reload_poll()

    def _restart_process_for_hot_reload(self) -> None:
        if self._launcher_path is None:
            self._append_home_log("WARN", "hot_reload_skipped missing_launcher")
            self._schedule_hot_reload_poll()
            return
        subprocess.Popen(
            [sys.executable, str(self._launcher_path)],
            cwd=str(self._project_root),
        )
        self._shutdown(silent=True)

    def _shutdown(self, silent: bool = False) -> None:
        if self._hot_reload_job is not None:
            self._root.after_cancel(self._hot_reload_job)
            self._hot_reload_job = None
        if self._auto_tick_job is not None:
            self._root.after_cancel(self._auto_tick_job)
            self._auto_tick_job = None
        self._auto_battle_service.stop()
        if not silent:
            self._append_home_log("INFO", "tool_closed")
        self._root.destroy()

    def _on_close(self) -> None:
        self._shutdown()


def launch_manual_coordinate_probe(project_root: Path) -> None:
    root = tk.Tk()
    app = ManualCoordinateProbeApp(
        root=root,
        probe_service=ManualCoordinateProbeService(project_root),
        calibration_store=ButtonCalibrationStore(project_root),
        auto_battle_service=AutoBattleService(project_root),
        recognition_workbench_service=RecognitionWorkbenchService(project_root),
    )
    _ = app
    root.mainloop()
