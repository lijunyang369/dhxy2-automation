from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .widgets import (
    build_action_toolbar,
    build_dual_preview_panel,
    build_log_panel,
    build_metric_card,
    build_status_grid,
)


class BasePageController:
    page_name = ""

    def __init__(self, app, parent: ttk.Frame) -> None:
        self.app = app
        self.parent = parent
        self.frame = ttk.Frame(parent)

    def build(self) -> ttk.Frame:
        raise NotImplementedError


class HomePageController(BasePageController):
    page_name = "home"

    def build(self) -> ttk.Frame:
        frame = self.frame
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        hero = ttk.Frame(frame, padding=20)
        hero.grid(row=0, column=0, sticky="ew")
        ttk.Label(hero, text="大话西游2自动化运行平台", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            hero,
            text="把校准、识别验证、自动战斗和运行复盘收束到一个桌面控制台里。",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(8, 6))
        ttk.Label(
            hero,
            text="当前仍是单机工作台架构，但页面组织已经按后续平台化的总览台、校准台、识别台、运行台来排。",
            style="Muted.TLabel",
            wraplength=980,
            justify=tk.LEFT,
        ).pack(anchor="w")

        build_action_toolbar(
            hero,
            (
                ("进入校准台", lambda: self.app._show_page("probe"), "Accent.TButton"),
                ("进入识别台", lambda: self.app._show_page("recognition"), None),
                ("进入运行台", lambda: self.app._show_page("auto_battle"), None),
            ),
            pady=(16, 0),
        )

        cards = ttk.Frame(frame)
        cards.grid(row=1, column=0, sticky="nsew", pady=(8, 12))
        for index in range(3):
            cards.columnconfigure(index, weight=1)

        build_metric_card(cards, 0, "校准资产", "按钮坐标与人工判定", self.app._summary_var)
        build_metric_card(cards, 1, "识别工作台", "模板、区域与 OCR 调试", self.app._recognition_config_path_var)
        build_metric_card(cards, 2, "运行状态", "会话与运行日志路径", self.app._auto_runtime_log_var)

        self.app._home_log_widget = build_log_panel(frame, "控制台事件流", row=2, height=20)
        return frame


class ProbePageController(BasePageController):
    page_name = "probe"

    def build(self) -> ttk.Frame:
        frame = self.frame
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        build_action_toolbar(
            frame,
            (
                ("返回总览", lambda: self.app._show_page("home"), None),
                ("刷新配置", self.app._reload_entries, None),
                ("保存坐标/状态", self.app._save_calibration, "Accent.TButton"),
                ("点击并截图", self.app._run_probe, None),
                ("保存判定", self.app._save_feedback, None),
            ),
            row=0,
            columnspan=2,
        )

        left_panel = ttk.Frame(frame)
        left_panel.grid(row=1, column=0, sticky="nsw", padx=(0, 16))
        left_panel.columnconfigure(0, weight=1)
        self._build_button_lists(left_panel)

        right_panel = ttk.Frame(frame)
        right_panel.grid(row=1, column=1, sticky="nsew")
        right_panel.columnconfigure(1, weight=1)
        right_panel.columnconfigure(2, weight=1)
        right_panel.rowconfigure(8, weight=1)
        right_panel.rowconfigure(9, weight=1)
        self._build_detail_panel(right_panel)
        return frame

    def _build_button_lists(self, parent: ttk.Frame) -> None:
        specs = (
            ("character_battle", "角色战斗指令", 10),
            ("pet_battle", "宠物战斗指令", 6),
            ("nonbattle", "非战斗界面", 18),
        )
        for index, (category, title, height) in enumerate(specs):
            frame = ttk.LabelFrame(parent, text=title, padding=8)
            frame.grid(row=index, column=0, sticky="nsew", pady=(0 if index == 0 else 12, 0))
            listbox = tk.Listbox(frame, width=42, height=height)
            listbox.pack(fill=tk.BOTH, expand=True)
            listbox.bind("<<ListboxSelect>>", lambda _event, current=category: self.app._on_select_entry(current))
            self.app._listboxes[category] = listbox

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        self.app._add_readonly_entry(parent, 0, "配置文件", self.app._config_path_var)
        self.app._add_readonly_entry(parent, 1, "按钮引用", self.app._button_ref_var)
        self.app._add_readonly_entry(parent, 2, "分组/按钮", self.app._button_name_var)
        self.app._add_entry(parent, 3, "显示名称", self.app._label_var)
        self.app._add_entry(parent, 4, "客户端 X", self.app._x_var)
        self.app._add_entry(parent, 5, "客户端 Y", self.app._y_var)
        self.app._add_entry(parent, 6, "点击延迟", self.app._delay_var)

        ttk.Label(parent, text="有效状态").grid(row=7, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(
            parent,
            textvariable=self.app._status_var,
            values=self.app.STATUS_OPTIONS,
            state="readonly",
        ).grid(row=7, column=1, sticky="ew", pady=(6, 0))

        ttk.Label(parent, text="人工判定备注").grid(row=8, column=0, sticky="nw", pady=(8, 0))
        notes = tk.Text(parent, height=8, wrap=tk.WORD)
        notes.grid(row=8, column=1, sticky="nsew", pady=(8, 0))
        self.app._notes_widget = notes

        before_label, after_label = build_dual_preview_panel(parent, "截图预览", row=8, column=2)
        self.app._before_preview_label = before_label
        self.app._after_preview_label = after_label

        self.app._add_readonly_entry(parent, 9, "前置截图", self.app._before_path_var)
        self.app._add_readonly_entry(parent, 10, "后置截图", self.app._after_path_var)
        self.app._add_readonly_entry(parent, 11, "记录文件", self.app._record_path_var)
        ttk.Label(
            parent,
            textvariable=self.app._result_var,
            foreground="#0a5",
            wraplength=720,
            justify=tk.LEFT,
        ).grid(row=12, column=0, columnspan=2, sticky="w", pady=(12, 0))


class RecognitionPageController(BasePageController):
    page_name = "recognition"

    def build(self) -> ttk.Frame:
        frame = self.frame
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(1, weight=1)

        build_action_toolbar(
            frame,
            (
                ("返回总览", lambda: self.app._show_page("home"), None),
                ("检测当前模块", self.app._run_selected_recognition_capture, "Accent.TButton"),
                ("检测全部模块", self.app._run_recognition_capture, None),
                ("保存截图区域", self.app._save_recognition_region, None),
                ("保存回合数字模板", self.app._save_round_digit_template, None),
            ),
            row=0,
            columnspan=3,
        )

        left_panel = ttk.LabelFrame(frame, text="识别模块列表", padding=8)
        left_panel.grid(row=1, column=0, sticky="nsw", padx=(0, 16))
        listbox = tk.Listbox(left_panel, width=34, height=20)
        listbox.pack(fill=tk.BOTH, expand=True)
        listbox.bind("<<ListboxSelect>>", self.app._on_select_recognition_module)
        self.app._recognition_listbox = listbox
        self.app._populate_recognition_module_listbox()

        right_panel = ttk.Frame(frame)
        right_panel.grid(row=1, column=1, sticky="nsew")
        right_panel.columnconfigure(1, weight=1)
        right_panel.rowconfigure(18, weight=1)

        self.app._add_readonly_entry(right_panel, 0, "模块 ID", self.app._recognition_module_id_var)
        self.app._add_readonly_entry(right_panel, 1, "区域名称", self.app._recognition_region_var)
        self.app._add_readonly_entry(right_panel, 2, "识别模式", self.app._recognition_mode_var)
        self.app._add_readonly_entry(right_panel, 3, "识别结果", self.app._recognition_detected_var)
        self.app._add_readonly_entry(right_panel, 4, "置信度", self.app._recognition_confidence_var)
        self.app._add_readonly_entry(right_panel, 5, "结果摘要", self.app._recognition_summary_text_var)
        self.app._add_readonly_entry(right_panel, 6, "场景配置", self.app._recognition_config_path_var)
        self.app._add_entry(right_panel, 7, "左边界", self.app._recognition_left_var)
        self.app._add_entry(right_panel, 8, "上边界", self.app._recognition_top_var)
        self.app._add_entry(right_panel, 9, "右边界", self.app._recognition_right_var)
        self.app._add_entry(right_panel, 10, "下边界", self.app._recognition_bottom_var)
        self.app._add_entry(right_panel, 11, "回合数字", self.app._recognition_round_digit_var)
        self.app._add_readonly_entry(right_panel, 13, "整图路径", self.app._recognition_full_path_var)
        self.app._add_readonly_entry(right_panel, 14, "裁图区路径", self.app._recognition_crop_path_var)
        self.app._add_readonly_entry(right_panel, 15, "模板路径", self.app._recognition_template_path_var)
        self.app._add_readonly_entry(right_panel, 16, "模板状态", self.app._recognition_round_template_status_var)
        self.app._add_readonly_entry(right_panel, 17, "记录文件", self.app._recognition_record_path_var)

        self.app._recognition_log_widget = build_log_panel(right_panel, "模块详情", row=18, height=12, columnspan=2)

        preview_panel = ttk.LabelFrame(frame, text="证据预览", padding=8)
        preview_panel.grid(row=1, column=2, sticky="nsew")
        preview_panel.columnconfigure(0, weight=1)
        preview_panel.rowconfigure(1, weight=1)
        preview_panel.rowconfigure(3, weight=1)
        preview_panel.rowconfigure(5, weight=1)
        ttk.Label(preview_panel, text="整图").grid(row=0, column=0, sticky="w")
        self.app._recognition_full_preview_label = ttk.Label(preview_panel, text="暂无图片", anchor="center")
        self.app._recognition_full_preview_label.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        ttk.Label(preview_panel, text="裁图区").grid(row=2, column=0, sticky="w")
        self.app._recognition_crop_preview_label = ttk.Label(preview_panel, text="暂无图片", anchor="center")
        self.app._recognition_crop_preview_label.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        ttk.Label(preview_panel, text="模板").grid(row=4, column=0, sticky="w")
        self.app._recognition_template_preview_label = ttk.Label(preview_panel, text="暂无模板", anchor="center")
        self.app._recognition_template_preview_label.grid(row=5, column=0, sticky="nsew")
        return frame


class AutoBattlePageController(BasePageController):
    page_name = "auto_battle"

    def build(self) -> ttk.Frame:
        frame = self.frame
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)

        build_action_toolbar(
            frame,
            (
                ("返回总览", lambda: self.app._show_page("home"), None),
                ("启动运行", self.app._start_auto_battle, "Accent.TButton"),
                ("停止运行", self.app._stop_auto_battle, None),
                ("清空日志", self.app._clear_battle_log, None),
            ),
            row=0,
            columnspan=2,
            leading_check=("开启自动战斗", self.app._auto_enabled_var),
        )

        summary = ttk.LabelFrame(frame, text="运行总览", padding=12)
        summary.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        build_status_grid(
            summary,
            (
                ("运行状态", self.app._auto_status_var, 0, 0, 1),
                ("轮次", self.app._auto_tick_var, 0, 2, 1),
                ("战斗状态", self.app._auto_state_var, 1, 0, 1),
                ("反馈结果", self.app._auto_feedback_var, 1, 2, 1),
                ("会话目录", self.app._auto_session_var, 2, 0, 3),
                ("运行日志", self.app._auto_runtime_log_var, 3, 0, 3),
            ),
        )

        hints = ttk.LabelFrame(frame, text="操作提示", padding=12)
        hints.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        hints.columnconfigure(0, weight=1)
        ttk.Label(
            hints,
            text="推荐流程\n1. 在校准台确认按钮坐标\n2. 在识别台确认模板与区域\n3. 回到这里启动自动战斗\n4. 用日志判断回合流与动作反馈",
            justify=tk.LEFT,
            wraplength=420,
        ).grid(row=0, column=0, sticky="nw")

        self.app._battle_log_widget = build_log_panel(frame, "战斗事件流", row=2, height=28, columnspan=2)
        return frame


def build_page_controllers(app, parent: ttk.Frame) -> dict[str, BasePageController]:
    controllers = {
        "home": HomePageController(app, parent),
        "probe": ProbePageController(app, parent),
        "recognition": RecognitionPageController(app, parent),
        "auto_battle": AutoBattlePageController(app, parent),
    }
    for controller in controllers.values():
        controller.build()
    return controllers
