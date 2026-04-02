from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .widgets import (
    build_action_toolbar,
    build_dashboard_tile,
    build_dual_preview_panel,
    build_hud_rule,
    build_log_panel,
    build_metric_card,
    build_single_preview_panel,
    build_status_badge,
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
        frame.rowconfigure(3, weight=1)

        hero = ttk.Frame(frame, style="Hero.TFrame", padding=18)
        hero.grid(row=0, column=0, sticky="ew")
        hero.columnconfigure(0, weight=1)
        hero.columnconfigure(1, weight=0)
        ttk.Label(hero, text="\u5927\u8bdd\u897f\u6e382 // \u81ea\u52a8\u5316\u63a7\u5236\u77e9\u9635", style="HeroTitle.TLabel").grid(
            row=0,
            column=0,
            sticky="w",
        )
        ttk.Label(hero, text="[ \u672c\u5730\u6218\u672f\u63a7\u5236\u53f0 ]", style="Badge.TLabel").grid(
            row=0,
            column=1,
            sticky="e",
        )
        ttk.Label(
            hero,
            text="\u5c06\u6309\u94ae\u6821\u51c6\u3001\u89c6\u89c9\u8bc6\u522b\u3001\u81ea\u52a8\u6218\u6597\u548c\u8fd0\u884c\u4e8b\u4ef6\u6d41\u805a\u5408\u5230\u4e00\u5957\u79d1\u6280\u611f\u76d1\u63a7\u9762\u677f\u4e2d\u3002",
            style="HeroMuted.TLabel",
            wraplength=980,
            justify=tk.LEFT,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        build_hud_rule(hero, "//// \u4fe1\u53f7\u94fe\u63a5\uff1a\u6821\u51c6 | \u8bc6\u522b | \u6267\u884c | \u8fd0\u884c\u9065\u6d4b ////", row=2, columnspan=2, pady=(8, 6))

        action_host = ttk.Frame(hero, style="Hero.TFrame")
        action_host.grid(row=3, column=0, sticky="w", pady=(8, 0))
        build_action_toolbar(
            action_host,
            (
                ("\u6821\u51c6\u53f0", lambda: self.app._show_page("probe"), "Accent.TButton"),
                ("\u8bc6\u522b\u53f0", lambda: self.app._show_page("recognition"), None),
                ("\u8fd0\u884c\u53f0", lambda: self.app._show_page("auto_battle"), None),
            ),
            pady=(0, 0),
        )
        self.app._home_status_badge_label = build_status_badge(hero, "\u7a7a\u95f2", row=3, column=1, sticky="e")

        ttk.Label(frame, text="[ \u5b9e\u65f6\u603b\u89c8 ]", style="Section.TLabel").grid(row=1, column=0, sticky="w", pady=(18, 8))
        top_strip = ttk.Frame(frame)
        top_strip.grid(row=2, column=0, sticky="ew")
        for index in range(4):
            top_strip.columnconfigure(index, weight=1)

        build_dashboard_tile(top_strip, 0, "\u6309\u94ae\u8d44\u4ea7", self.app._summary_var, "\u68c0\u67e5\u6807\u6ce8\u548c\u5750\u6807\u6570\u636e\u662f\u5426\u53ef\u7528")
        build_dashboard_tile(top_strip, 1, "\u8bc6\u522b\u573a\u666f", self.app._recognition_config_display_var, "\u786e\u8ba4 OCR \u548c\u6a21\u677f\u573a\u666f\u914d\u7f6e")
        build_dashboard_tile(top_strip, 2, "\u8fd0\u884c\u65e5\u5fd7", self.app._auto_runtime_log_display_var, "\u76f4\u8fde\u5f53\u524d\u4f1a\u8bdd\u7684\u8fd0\u884c\u65e5\u5fd7")
        build_dashboard_tile(top_strip, 3, "\u5f53\u524d\u4f1a\u8bdd", self.app._auto_session_display_var, "\u672a\u542f\u52a8\u4f1a\u8bdd\u65f6\u8fd9\u91cc\u4f1a\u663e\u793a\u9ed8\u8ba4\u63d0\u793a")

        bottom = ttk.Frame(frame)
        bottom.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)
        bottom.rowconfigure(0, weight=1)

        left = ttk.Frame(bottom)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)

        right = ttk.Frame(bottom)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)

        build_metric_card(
            left,
            0,
            "\u5de5\u4f5c\u6d41\u72b6\u6001",
            "\u6821\u51c6\u8d1f\u8d23\u6309\u94ae\u51c6\u786e\u6027\uff0c\u8bc6\u522b\u8d1f\u8d23\u89c2\u6d4b\u53ef\u9760\u6027\uff0c\u8fd0\u884c\u53f0\u8d1f\u8d23\u6301\u7eed\u6267\u884c\u3002",
            self.app._auto_status_var,
        )
        self.app._home_log_widget = build_log_panel(left, "\u5e73\u53f0\u4e8b\u4ef6\u6d41", row=1, height=18)

        handbook = ttk.LabelFrame(right, text="\u63a7\u5236\u53f0\u8bf4\u660e", padding=14)
        handbook.grid(row=0, column=0, sticky="nsew")
        handbook.columnconfigure(0, weight=1)
        ttk.Label(
            handbook,
            text="\u63a8\u8350\u4f7f\u7528\u987a\u5e8f\n1. \u5148\u5728\u6821\u51c6\u53f0\u786e\u8ba4\u6309\u94ae\u5750\u6807\u548c\u72b6\u6001\n2. \u5728\u8bc6\u522b\u53f0\u68c0\u67e5\u622a\u56fe\u533a\u57df\u3001\u56de\u5408\u6570\u5b57\u6a21\u677f\u548c\u8bc6\u522b\u7ed3\u679c\n3. \u5728\u8fd0\u884c\u53f0\u542f\u52a8\u81ea\u52a8\u6218\u6597\uff0c\u76ef\u7d27\u4e8b\u4ef6\u65e5\u5fd7\n4. \u51fa\u73b0\u95ee\u9898\u65f6\uff0c\u4f18\u5148\u4ece\u8bc6\u522b\u622a\u56fe\u548c runtime.log \u56de\u6eaf",
            justify=tk.LEFT,
            wraplength=400,
        ).grid(row=0, column=0, sticky="nw")
        return frame


class ProbePageController(BasePageController):
    page_name = "probe"

    def build(self) -> ttk.Frame:
        frame = self.frame
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(1, weight=1)

        ttk.Label(frame, text="[ \u6821\u51c6\u8282\u70b9 // \u6a21\u7ec4-11 ]", style="Section.TLabel").grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 8),
        )
        build_hud_rule(frame, "//// \u6307\u9488\u6620\u5c04 // \u70b9\u51fb\u63a2\u9488 // \u53cd\u9988\u6807\u6ce8 ////", row=1, columnspan=2)

        build_action_toolbar(
            frame,
            (
                ("\u8fd4\u56de\u603b\u89c8", lambda: self.app._show_page("home"), None),
                ("\u5237\u65b0\u914d\u7f6e", self.app._reload_entries, None),
                ("\u4fdd\u5b58\u5750\u6807\u4e0e\u72b6\u6001", self.app._save_calibration, "Accent.TButton"),
                ("\u70b9\u51fb\u5e76\u622a\u56fe", self.app._run_probe, None),
                ("\u4fdd\u5b58\u5224\u5b9a", self.app._save_feedback, None),
            ),
            row=2,
            columnspan=2,
        )

        left_panel = ttk.Frame(frame)
        left_panel.grid(row=3, column=0, sticky="nsw", padx=(0, 16))
        left_panel.columnconfigure(0, weight=1)
        self._build_button_lists(left_panel)

        right_panel = ttk.Frame(frame)
        right_panel.grid(row=3, column=1, sticky="nsew")
        right_panel.columnconfigure(1, weight=1)
        right_panel.columnconfigure(2, weight=1)
        right_panel.rowconfigure(8, weight=1)
        right_panel.rowconfigure(9, weight=1)
        self._build_detail_panel(right_panel)
        return frame

    def _build_button_lists(self, parent: ttk.Frame) -> None:
        specs = (
            ("character_battle", "\u89d2\u8272\u6218\u6597\u6307\u4ee4", 10),
            ("pet_battle", "\u5ba0\u7269\u6218\u6597\u6307\u4ee4", 6),
            ("nonbattle", "\u975e\u6218\u6597\u754c\u9762", 18),
        )
        for index, (category, title, height) in enumerate(specs):
            frame = ttk.LabelFrame(parent, text=title, padding=8)
            frame.grid(row=index, column=0, sticky="nsew", pady=(0 if index == 0 else 12, 0))
            listbox = tk.Listbox(
                frame,
                width=42,
                height=height,
                bg="#16283d",
                fg="#edf3fb",
                selectbackground="#37b7a8",
                selectforeground="#071512",
                relief="flat",
                highlightthickness=0,
            )
            listbox.pack(fill=tk.BOTH, expand=True)
            listbox.bind("<<ListboxSelect>>", lambda _event, current=category: self.app._on_select_entry(current))
            self.app._listboxes[category] = listbox

    def _build_detail_panel(self, parent: ttk.Frame) -> None:
        self.app._add_readonly_entry(parent, 0, "\u914d\u7f6e\u6587\u4ef6", self.app._config_path_var)
        self.app._add_readonly_entry(parent, 1, "\u6309\u94ae\u5f15\u7528", self.app._button_ref_var)
        self.app._add_readonly_entry(parent, 2, "\u5206\u7ec4\u4e0e\u6309\u94ae", self.app._button_name_var)
        self.app._add_entry(parent, 3, "\u663e\u793a\u540d\u79f0", self.app._label_var)
        self.app._add_entry(parent, 4, "\u5ba2\u6237\u7aef X", self.app._x_var)
        self.app._add_entry(parent, 5, "\u5ba2\u6237\u7aef Y", self.app._y_var)
        self.app._add_entry(parent, 6, "\u70b9\u51fb\u5ef6\u8fdf", self.app._delay_var)

        ttk.Label(parent, text="\u6709\u6548\u72b6\u6001").grid(row=7, column=0, sticky="w", pady=(6, 0))
        ttk.Combobox(parent, textvariable=self.app._status_var, values=self.app.STATUS_OPTIONS, state="readonly").grid(
            row=7,
            column=1,
            sticky="ew",
            pady=(6, 0),
        )

        ttk.Label(parent, text="\u4eba\u5de5\u5224\u5b9a\u5907\u6ce8").grid(row=8, column=0, sticky="nw", pady=(8, 0))
        notes = tk.Text(
            parent,
            height=8,
            wrap=tk.WORD,
            bg="#16283d",
            fg="#edf3fb",
            insertbackground="#edf3fb",
            relief="flat",
            highlightthickness=0,
            padx=10,
            pady=10,
        )
        notes.grid(row=8, column=1, sticky="nsew", pady=(8, 0))
        self.app._notes_widget = notes

        before_label, after_label = build_dual_preview_panel(parent, "\u622a\u56fe\u9884\u89c8", row=8, column=2)
        self.app._before_preview_label = before_label
        self.app._after_preview_label = after_label

        self.app._add_readonly_entry(parent, 9, "\u64cd\u4f5c\u524d\u622a\u56fe", self.app._before_path_var)
        self.app._add_readonly_entry(parent, 10, "\u64cd\u4f5c\u540e\u622a\u56fe", self.app._after_path_var)
        self.app._add_readonly_entry(parent, 11, "\u8bb0\u5f55\u6587\u4ef6", self.app._record_path_var)
        ttk.Label(
            parent,
            textvariable=self.app._result_var,
            foreground="#37b7a8",
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

        ttk.Label(frame, text="[ \u8bc6\u522b\u8282\u70b9 // \u6a21\u7ec4-21 ]", style="Section.TLabel").grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 8),
        )
        build_hud_rule(frame, "//// OCR \u533a\u57df\u68c0\u67e5 // \u6a21\u677f\u5339\u914d // \u56de\u5408\u6570\u5b57\u5feb\u7167 ////", row=1, columnspan=3)

        build_action_toolbar(
            frame,
            (
                ("\u8fd4\u56de\u603b\u89c8", lambda: self.app._show_page("home"), None),
                ("\u68c0\u6d4b\u5f53\u524d\u6a21\u5757", self.app._run_selected_recognition_capture, "Accent.TButton"),
                ("\u68c0\u6d4b\u5168\u90e8\u6a21\u5757", self.app._run_recognition_capture, None),
                ("\u4fdd\u5b58\u622a\u56fe\u533a\u57df", self.app._save_recognition_region, None),
                ("\u4fdd\u5b58\u56de\u5408\u6570\u5b57\u6a21\u677f", self.app._save_round_digit_template, None),
            ),
            row=2,
            columnspan=3,
        )

        left_panel = ttk.LabelFrame(frame, text="\u8bc6\u522b\u6a21\u5757\u5217\u8868", padding=8)
        left_panel.grid(row=3, column=0, sticky="nsw", padx=(0, 16))
        listbox = tk.Listbox(
            left_panel,
            width=34,
            height=20,
            bg="#16283d",
            fg="#edf3fb",
            selectbackground="#37b7a8",
            selectforeground="#071512",
            relief="flat",
            highlightthickness=0,
        )
        listbox.pack(fill=tk.BOTH, expand=True)
        listbox.bind("<<ListboxSelect>>", self.app._on_select_recognition_module)
        self.app._recognition_listbox = listbox
        self.app._populate_recognition_module_listbox()

        right_panel = ttk.Frame(frame)
        right_panel.grid(row=3, column=1, sticky="nsew")
        right_panel.columnconfigure(1, weight=1)
        right_panel.rowconfigure(18, weight=1)

        self.app._add_readonly_entry(right_panel, 0, "\u6a21\u5757 ID", self.app._recognition_module_id_var)
        self.app._add_readonly_entry(right_panel, 1, "\u533a\u57df\u540d\u79f0", self.app._recognition_region_var)
        self.app._add_readonly_entry(right_panel, 2, "\u8bc6\u522b\u6a21\u5f0f", self.app._recognition_mode_var)
        self.app._add_readonly_entry(right_panel, 3, "\u8bc6\u522b\u7ed3\u679c", self.app._recognition_detected_var)
        self.app._add_readonly_entry(right_panel, 4, "\u7f6e\u4fe1\u5ea6", self.app._recognition_confidence_var)
        self.app._add_readonly_entry(right_panel, 5, "\u7ed3\u679c\u6458\u8981", self.app._recognition_summary_text_var)
        self.app._add_readonly_entry(right_panel, 6, "\u573a\u666f\u914d\u7f6e", self.app._recognition_config_path_var)
        self.app._add_entry(right_panel, 7, "\u5de6\u8fb9\u754c", self.app._recognition_left_var)
        self.app._add_entry(right_panel, 8, "\u4e0a\u8fb9\u754c", self.app._recognition_top_var)
        self.app._add_entry(right_panel, 9, "\u53f3\u8fb9\u754c", self.app._recognition_right_var)
        self.app._add_entry(right_panel, 10, "\u4e0b\u8fb9\u754c", self.app._recognition_bottom_var)
        self.app._add_entry(right_panel, 11, "\u56de\u5408\u6570\u5b57", self.app._recognition_round_digit_var)
        self.app._add_readonly_entry(right_panel, 13, "\u6574\u56fe\u8def\u5f84", self.app._recognition_full_path_var)
        self.app._add_readonly_entry(right_panel, 14, "\u88c1\u56fe\u533a\u8def\u5f84", self.app._recognition_crop_path_var)
        self.app._add_readonly_entry(right_panel, 15, "\u6a21\u677f\u8def\u5f84", self.app._recognition_template_path_var)
        self.app._add_readonly_entry(right_panel, 16, "\u6a21\u677f\u72b6\u6001", self.app._recognition_round_template_status_var)
        self.app._add_readonly_entry(right_panel, 17, "\u8bb0\u5f55\u6587\u4ef6", self.app._recognition_record_path_var)
        self.app._recognition_log_widget = build_log_panel(right_panel, "\u6a21\u5757\u8be6\u60c5", row=18, height=12, columnspan=2)

        preview_panel = ttk.LabelFrame(frame, text="\u8bc1\u636e\u9884\u89c8", padding=10)
        preview_panel.grid(row=3, column=2, sticky="nsew")
        preview_panel.columnconfigure(0, weight=1)
        preview_panel.rowconfigure(1, weight=1)
        preview_panel.rowconfigure(3, weight=1)
        preview_panel.rowconfigure(5, weight=1)
        ttk.Label(preview_panel, text="\u6574\u56fe").grid(row=0, column=0, sticky="w")
        self.app._recognition_full_preview_label = ttk.Label(preview_panel, text="\u6682\u65e0\u56fe\u7247", anchor="center", style="Surface.TLabel", padding=12)
        self.app._recognition_full_preview_label.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        ttk.Label(preview_panel, text="\u88c1\u56fe\u533a").grid(row=2, column=0, sticky="w")
        self.app._recognition_crop_preview_label = ttk.Label(preview_panel, text="\u6682\u65e0\u56fe\u7247", anchor="center", style="Surface.TLabel", padding=12)
        self.app._recognition_crop_preview_label.grid(row=3, column=0, sticky="nsew", pady=(0, 8))
        ttk.Label(preview_panel, text="\u6a21\u677f").grid(row=4, column=0, sticky="w")
        self.app._recognition_template_preview_label = ttk.Label(preview_panel, text="\u6682\u65e0\u6a21\u677f", anchor="center", style="Surface.TLabel", padding=12)
        self.app._recognition_template_preview_label.grid(row=5, column=0, sticky="nsew")
        return frame


class AutoBattlePageController(BasePageController):
    page_name = "auto_battle"

    def build(self) -> ttk.Frame:
        frame = self.frame
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        build_action_toolbar(
            frame,
            (
                ("\u8fd4\u56de\u603b\u89c8", lambda: self.app._show_page("home"), None),
                ("\u542f\u52a8\u8fd0\u884c", self.app._start_auto_battle, "Accent.TButton"),
                ("\u505c\u6b62\u8fd0\u884c", self.app._stop_auto_battle, None),
                ("\u6e05\u7a7a\u65e5\u5fd7", self.app._clear_battle_log, None),
            ),
            row=0,
            columnspan=1,
            leading_check=("\u5f00\u542f\u81ea\u52a8\u6218\u6597", self.app._auto_enabled_var),
        )

        ttk.Label(frame, text="[ \u6218\u6597\u63a7\u5236\u9762\u677f ]", style="Section.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 4))
        build_hud_rule(frame, "//// \u6218\u6597\u5faa\u73af // \u4f1a\u8bdd\u8ffd\u8e2a // \u52a8\u4f5c\u53cd\u9988 // \u89c6\u89c9\u8bc1\u636e ////", row=2)

        dashboard = ttk.Frame(frame)
        dashboard.grid(row=3, column=0, sticky="nsew")
        dashboard.columnconfigure(0, weight=3)
        dashboard.columnconfigure(1, weight=2)
        dashboard.rowconfigure(1, weight=1)

        strip = ttk.Frame(dashboard)
        strip.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        for index in range(4):
            strip.columnconfigure(index, weight=1)

        badges = ttk.Frame(dashboard)
        badges.grid(row=0, column=1, sticky="e", pady=(0, 12))
        badges.columnconfigure(1, weight=1)
        ttk.Label(badges, text="\u8fd0\u884c\u6807\u7b7e", style="Muted.TLabel").grid(row=0, column=0, sticky="e", padx=(0, 8))
        self.app._auto_status_badge_label = build_status_badge(badges, "\u7a7a\u95f2", row=0, column=1)

        build_dashboard_tile(strip, 0, "\u8fd0\u884c\u72b6\u6001", self.app._auto_status_var, "\u5f53\u524d\u4f1a\u8bdd\u662f\u5426\u5728\u8fd0\u884c")
        build_dashboard_tile(strip, 1, "\u6218\u6597\u72b6\u6001", self.app._auto_state_var, "\u89c2\u5bdf\u5230\u7684\u6218\u6597\u9636\u6bb5")
        build_dashboard_tile(strip, 2, "\u6700\u65b0\u53cd\u9988", self.app._auto_feedback_var, "\u6700\u8fd1\u4e00\u6b21\u6267\u884c\u7684\u7ed3\u679c")
        build_dashboard_tile(strip, 3, "\u8f6e\u8be2\u8f6e\u6b21", self.app._auto_tick_var, "\u7528\u6765\u5224\u65ad\u8fd0\u884c\u8282\u594f\u662f\u5426\u6b63\u5e38")

        left = ttk.Frame(dashboard)
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        summary = ttk.LabelFrame(left, text="\u4f1a\u8bdd\u4e0e\u8fd0\u884c\u4e0a\u4e0b\u6587", padding=12)
        summary.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        build_status_grid(
            summary,
            (
                ("\u4f1a\u8bdd\u76ee\u5f55", self.app._auto_session_var, 0, 0, 3),
                ("\u8fd0\u884c\u65e5\u5fd7", self.app._auto_runtime_log_var, 1, 0, 3),
            ),
        )

        self.app._battle_log_widget = build_log_panel(left, "\u6218\u6597\u4e8b\u4ef6\u65f6\u95f4\u7ebf", row=1, height=28)

        right = ttk.Frame(dashboard)
        right.grid(row=1, column=1, sticky="nsew", padx=(8, 0))
        right.columnconfigure(0, weight=1)

        evidence = ttk.LabelFrame(right, text="\u6700\u65b0\u8fd0\u884c\u8bc1\u636e", padding=14)
        evidence.grid(row=0, column=0, sticky="ew")
        build_status_grid(
            evidence,
            (
                ("\u5f53\u524d\u573a\u666f", self.app._auto_scene_var, 0, 0, 1),
                ("\u5f53\u524d\u56de\u5408", self.app._auto_round_var, 0, 2, 1),
                ("\u6700\u65b0\u7b56\u7565", self.app._auto_plan_var, 1, 0, 3),
                ("\u8bc1\u636e\u8def\u5f84", self.app._auto_evidence_var, 2, 0, 3),
            ),
        )

        playbook = ttk.LabelFrame(right, text="\u8fd0\u7ef4\u624b\u518c", padding=14)
        playbook.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        playbook.columnconfigure(0, weight=1)
        ttk.Label(
            playbook,
            text="\u6807\u51c6\u64cd\u4f5c\n1. \u5f00\u542f\u81ea\u52a8\u6218\u6597\u540e\u518d\u542f\u52a8\u8fd0\u884c\n2. \u89c2\u5bdf\u8fd0\u884c\u72b6\u6001\u3001\u6218\u6597\u72b6\u6001\u548c\u6700\u65b0\u53cd\u9988\n3. \u5982\u679c\u8f6e\u6b21\u4e0d\u589e\u957f\uff0c\u5148\u68c0\u67e5\u7a97\u53e3\u805a\u7126\u4e0e\u8bc6\u522b\u6210\u679c\n4. \u5982\u679c\u53cd\u9988\u5f02\u5e38\uff0c\u56de\u5230\u6821\u51c6\u53f0\u6216\u8bc6\u522b\u53f0\u91cd\u65b0\u68c0\u67e5",
            justify=tk.LEFT,
            wraplength=420,
        ).grid(row=0, column=0, sticky="nw")

        diagnostics = ttk.LabelFrame(right, text="\u5feb\u901f\u5224\u65ad", padding=14)
        diagnostics.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        diagnostics.columnconfigure(0, weight=1)
        ttk.Label(
            diagnostics,
            text="\u770b\u8fd9\u51e0\u4e2a\u4fe1\u53f7\n- \u8fd0\u884c\u72b6\u6001\u4e3a\u201c\u8fd0\u884c\u4e2d\u201d\u4f46\u4e8b\u4ef6\u7ebf\u65e0\u65b0\u8bb0\u5f55\uff1a\u68c0\u67e5\u7a97\u53e3\u6216\u622a\u56fe\u901a\u9053\n- \u6218\u6597\u72b6\u6001\u957f\u671f\u4e0d\u53d8\uff1a\u68c0\u67e5\u533a\u57df\u548c\u6a21\u677f\n- \u6700\u65b0\u53cd\u9988\u4e3a\u7a7a\uff1a\u8bf4\u660e\u8fd8\u6ca1\u6267\u884c\u5230\u6709\u6548\u52a8\u4f5c",
            justify=tk.LEFT,
            wraplength=420,
        ).grid(row=0, column=0, sticky="nw")

        self.app._auto_evidence_preview_label = build_single_preview_panel(
            right,
            "\u6700\u8fd1\u8bc6\u522b\u8bc1\u636e\u56fe",
            row=3,
            column=0,
        )
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
