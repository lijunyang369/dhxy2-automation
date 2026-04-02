from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def configure_workbench_theme(root: tk.Tk) -> None:
    root.configure(bg="#0b1220")
    root.option_add("*Font", ("Microsoft YaHei UI", 10))
    root.option_add("*TCombobox*Listbox.font", ("Microsoft YaHei UI", 10))

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    palette = {
        "bg": "#0b1220",
        "panel": "#111b2e",
        "panel_alt": "#16233a",
        "border": "#30415d",
        "text": "#e8edf7",
        "muted": "#95a4bf",
        "accent": "#d8b36a",
        "accent_soft": "#22304a",
        "success": "#4fbf8f",
    }

    style.configure(".", background=palette["bg"], foreground=palette["text"])
    style.configure("TFrame", background=palette["bg"])
    style.configure(
        "TLabel",
        background=palette["bg"],
        foreground=palette["text"],
    )
    style.configure(
        "Muted.TLabel",
        background=palette["bg"],
        foreground=palette["muted"],
    )
    style.configure(
        "Title.TLabel",
        background=palette["bg"],
        foreground=palette["text"],
        font=("Microsoft YaHei UI", 18, "bold"),
    )
    style.configure(
        "TLabelframe",
        background=palette["panel"],
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=palette["panel"],
        foreground=palette["accent"],
        font=("Microsoft YaHei UI", 10, "bold"),
    )
    style.configure(
        "TEntry",
        fieldbackground=palette["panel_alt"],
        foreground=palette["text"],
        insertcolor=palette["text"],
    )
    style.map(
        "TEntry",
        fieldbackground=[("readonly", palette["panel_alt"])],
        foreground=[("readonly", palette["text"])],
    )
    style.configure(
        "TCombobox",
        fieldbackground=palette["panel_alt"],
        foreground=palette["text"],
        arrowcolor=palette["accent"],
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", palette["panel_alt"])],
        foreground=[("readonly", palette["text"])],
    )
    style.configure(
        "TButton",
        background=palette["accent_soft"],
        foreground=palette["text"],
        borderwidth=0,
        focusthickness=0,
        padding=(12, 8),
    )
    style.map(
        "TButton",
        background=[("active", palette["accent"]), ("pressed", palette["accent"])],
        foreground=[("active", palette["bg"]), ("pressed", palette["bg"])],
    )
    style.configure(
        "Accent.TButton",
        background=palette["accent"],
        foreground=palette["bg"],
    )
    style.map(
        "Accent.TButton",
        background=[("active", "#ebc985"), ("pressed", "#ebc985")],
        foreground=[("active", palette["bg"]), ("pressed", palette["bg"])],
    )
    style.configure(
        "TCheckbutton",
        background=palette["bg"],
        foreground=palette["text"],
    )
