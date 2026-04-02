from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .theme import PALETTE


def build_action_toolbar(
    parent: ttk.Frame,
    actions,
    *,
    row: int = 0,
    columnspan: int = 1,
    pady=(0, 12),
    leading_check: tuple[str, tk.BooleanVar] | None = None,
) -> ttk.Frame:
    toolbar = ttk.Frame(parent, style="Surface.TFrame", padding=12)
    toolbar.grid(row=row, column=0, columnspan=columnspan, sticky="ew", pady=pady)
    if leading_check is not None:
        text, variable = leading_check
        ttk.Checkbutton(toolbar, text=text, variable=variable).pack(side=tk.LEFT, padx=(0, 16))
    for index, (label, command, style_name) in enumerate(actions):
        kwargs = {"text": label, "command": command}
        if style_name:
            kwargs["style"] = style_name
        ttk.Button(toolbar, **kwargs).pack(side=tk.LEFT, padx=(0 if index == 0 and leading_check is None else 10, 0), ipadx=8)
    return toolbar


def build_log_panel(
    parent: ttk.Frame,
    title: str,
    *,
    row: int,
    height: int,
    columnspan: int = 1,
) -> tk.Text:
    frame = ttk.LabelFrame(parent, text=title, padding=10)
    frame.grid(row=row, column=0, columnspan=columnspan, sticky="nsew", pady=(12 if row else 0, 0))
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    widget = tk.Text(
        frame,
        wrap=tk.WORD,
        height=height,
        state="disabled",
        bg=PALETTE["surface_soft"],
        fg=PALETTE["text"],
        insertbackground=PALETTE["text"],
        relief="flat",
        highlightthickness=0,
        padx=12,
        pady=12,
        font=("Consolas", 10),
        spacing1=2,
        spacing3=3,
    )
    widget.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    widget.configure(yscrollcommand=scrollbar.set)
    widget.tag_configure("info", foreground=PALETTE["text"])
    widget.tag_configure("state", foreground=PALETTE["warn"])
    widget.tag_configure("action", foreground=PALETTE["accent"])
    widget.tag_configure("warn", foreground="#f0c36d")
    widget.tag_configure("error", foreground=PALETTE["danger"])
    return widget


def build_metric_card(parent: ttk.Frame, column: int, title: str, subtitle: str, variable) -> ttk.LabelFrame:
    card = ttk.LabelFrame(parent, text=title, padding=14)
    card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))
    card.columnconfigure(0, weight=1)
    ttk.Label(card, text=f"模组-{column + 1:02d}", style="HudCode.TLabel").grid(row=0, column=0, sticky="e")
    ttk.Label(card, text=subtitle, style="SurfaceMuted.TLabel", wraplength=260, justify=tk.LEFT).grid(
        row=1,
        column=0,
        sticky="w",
    )
    ttk.Label(card, textvariable=variable, style="Emphasis.TLabel", wraplength=260, justify=tk.LEFT).grid(
        row=2,
        column=0,
        sticky="nw",
        pady=(12, 0),
    )
    return card


def build_dashboard_tile(parent: ttk.Frame, column: int, title: str, value_var, caption: str) -> ttk.LabelFrame:
    card = ttk.LabelFrame(parent, text=title, padding=14)
    card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 10, 0))
    card.columnconfigure(0, weight=1)
    ttk.Label(card, text=f"分区-{column + 1:02d}", style="HudCode.TLabel").grid(row=0, column=0, sticky="e")
    ttk.Label(card, textvariable=value_var, style="KpiValue.TLabel", wraplength=200, justify=tk.LEFT).grid(
        row=1,
        column=0,
        sticky="nw",
    )
    ttk.Label(card, text=caption, style="KpiCaption.TLabel", wraplength=220, justify=tk.LEFT).grid(
        row=2,
        column=0,
        sticky="sw",
        pady=(8, 0),
    )
    return card


def build_hud_rule(parent: ttk.Frame, text: str, *, row: int, column: int = 0, columnspan: int = 1, pady=(6, 6)) -> ttk.Label:
    label = ttk.Label(parent, text=text, style="HudRule.TLabel")
    label.grid(row=row, column=column, columnspan=columnspan, sticky="ew", pady=pady)
    return label


def build_status_badge(parent: ttk.Frame, text: str, *, row: int, column: int, sticky: str = "e") -> ttk.Label:
    label = ttk.Label(parent, text=text, style="StatusIdle.TLabel")
    label.grid(row=row, column=column, sticky=sticky)
    return label


def build_status_grid(parent: ttk.LabelFrame, items) -> None:
    parent.columnconfigure(1, weight=1)
    parent.columnconfigure(3, weight=1)
    for label, variable, row, column, span in items:
        build_labeled_readonly(parent, row, column, label, variable, span=span)


def build_labeled_readonly(parent: ttk.Frame, row: int, column: int, label: str, variable, *, span: int = 1) -> None:
    ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=(8, 0))
    ttk.Entry(parent, textvariable=variable, state="readonly").grid(
        row=row,
        column=column + 1,
        columnspan=span,
        sticky="ew",
        pady=(8, 0),
        padx=(8, 0),
    )


def build_dual_preview_panel(parent: ttk.Frame, title: str, *, row: int, column: int) -> tuple[ttk.Label, ttk.Label]:
    preview_frame = ttk.LabelFrame(parent, text=title, padding=10)
    preview_frame.grid(row=row, column=column, rowspan=4, sticky="nsew", padx=(16, 0), pady=(8, 0))
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.columnconfigure(1, weight=1)
    preview_frame.rowconfigure(1, weight=1)
    ttk.Label(preview_frame, text="\u64cd\u4f5c\u524d").grid(row=0, column=0, sticky="w")
    ttk.Label(preview_frame, text="\u64cd\u4f5c\u540e").grid(row=0, column=1, sticky="w")
    before_label = ttk.Label(
        preview_frame,
        text="\u6682\u65e0\u56fe\u7247",
        anchor="center",
        style="Surface.TLabel",
        padding=12,
    )
    before_label.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
    after_label = ttk.Label(
        preview_frame,
        text="\u6682\u65e0\u56fe\u7247",
        anchor="center",
        style="Surface.TLabel",
        padding=12,
    )
    after_label.grid(row=1, column=1, sticky="nsew")
    return before_label, after_label


def build_single_preview_panel(parent: ttk.Frame, title: str, *, row: int, column: int) -> ttk.Label:
    preview_frame = ttk.LabelFrame(parent, text=title, padding=10)
    preview_frame.grid(row=row, column=column, sticky="nsew", pady=(12, 0))
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(0, weight=1)
    label = ttk.Label(
        preview_frame,
        text="\u6682\u65e0\u8bc1\u636e\u56fe",
        anchor="center",
        style="Surface.TLabel",
        padding=12,
    )
    label.grid(row=0, column=0, sticky="nsew")
    return label
