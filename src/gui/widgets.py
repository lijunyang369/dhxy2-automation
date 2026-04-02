from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_action_toolbar(
    parent: ttk.Frame,
    actions,
    *,
    row: int = 0,
    columnspan: int = 1,
    pady=(0, 12),
    leading_check: tuple[str, tk.BooleanVar] | None = None,
) -> ttk.Frame:
    toolbar = ttk.Frame(parent)
    toolbar.grid(row=row, column=0, columnspan=columnspan, sticky="ew", pady=pady)
    if leading_check is not None:
        text, variable = leading_check
        ttk.Checkbutton(toolbar, text=text, variable=variable).pack(side=tk.LEFT, padx=(0, 12))
    for index, (label, command, style) in enumerate(actions):
        kwargs = {"text": label, "command": command}
        if style:
            kwargs["style"] = style
        ttk.Button(toolbar, **kwargs).pack(side=tk.LEFT, padx=(0 if index == 0 and leading_check is None else 8, 0))
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
    widget = tk.Text(frame, wrap=tk.WORD, height=height, state="disabled")
    widget.grid(row=0, column=0, sticky="nsew")
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=widget.yview)
    scrollbar.grid(row=0, column=1, sticky="ns")
    widget.configure(yscrollcommand=scrollbar.set)
    return widget


def build_metric_card(parent: ttk.Frame, column: int, title: str, subtitle: str, variable) -> ttk.LabelFrame:
    card = ttk.LabelFrame(parent, text=title, padding=12)
    card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
    card.columnconfigure(0, weight=1)
    ttk.Label(card, text=subtitle, style="Muted.TLabel", wraplength=260, justify=tk.LEFT).grid(row=0, column=0, sticky="w")
    ttk.Label(card, textvariable=variable, wraplength=260, justify=tk.LEFT).grid(row=1, column=0, sticky="w", pady=(10, 0))
    return card


def build_status_grid(parent: ttk.LabelFrame, items) -> None:
    parent.columnconfigure(1, weight=1)
    parent.columnconfigure(3, weight=1)
    for label, variable, row, column, span in items:
        build_labeled_readonly(parent, row, column, label, variable, span=span)


def build_labeled_readonly(parent: ttk.Frame, row: int, column: int, label: str, variable, *, span: int = 1) -> None:
    ttk.Label(parent, text=label).grid(row=row, column=column, sticky="w", pady=(6, 0))
    ttk.Entry(parent, textvariable=variable, state="readonly").grid(
        row=row,
        column=column + 1,
        columnspan=span,
        sticky="ew",
        pady=(6, 0),
        padx=(8, 0),
    )


def build_dual_preview_panel(parent: ttk.Frame, title: str, *, row: int, column: int) -> tuple[ttk.Label, ttk.Label]:
    preview_frame = ttk.LabelFrame(parent, text=title, padding=8)
    preview_frame.grid(row=row, column=column, rowspan=4, sticky="nsew", padx=(16, 0), pady=(8, 0))
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.columnconfigure(1, weight=1)
    preview_frame.rowconfigure(1, weight=1)
    ttk.Label(preview_frame, text="操作前").grid(row=0, column=0, sticky="w")
    ttk.Label(preview_frame, text="操作后").grid(row=0, column=1, sticky="w")
    before_label = ttk.Label(preview_frame, text="暂无图片", anchor="center")
    before_label.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
    after_label = ttk.Label(preview_frame, text="暂无图片", anchor="center")
    after_label.grid(row=1, column=1, sticky="nsew")
    return before_label, after_label
