from __future__ import annotations

import tkinter as tk
from tkinter import ttk


PALETTE = {
    "bg": "#040812",
    "surface": "#09111d",
    "surface_alt": "#0d1828",
    "surface_soft": "#102338",
    "surface_strong": "#14314e",
    "border": "#1b5676",
    "border_soft": "#123247",
    "text": "#dff7ff",
    "muted": "#79a8bd",
    "accent": "#39d0ff",
    "accent_hover": "#69deff",
    "accent_text": "#041018",
    "warn": "#ffc857",
    "danger": "#ff6b8a",
}


def configure_workbench_theme(root: tk.Tk) -> None:
    root.configure(bg=PALETTE["bg"])
    root.option_add("*Font", ("Microsoft YaHei UI", 10))
    root.option_add("*TCombobox*Listbox.font", ("Microsoft YaHei UI", 10))

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.configure("TFrame", background=PALETTE["bg"])
    style.configure("Surface.TFrame", background=PALETTE["surface"])
    style.configure("Hero.TFrame", background=PALETTE["surface_alt"])
    style.configure("Card.TFrame", background=PALETTE["surface"])

    style.configure("TLabel", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.configure("Surface.TLabel", background=PALETTE["surface"], foreground=PALETTE["text"])
    style.configure("Hero.TLabel", background=PALETTE["surface_alt"], foreground=PALETTE["text"])
    style.configure("Muted.TLabel", background=PALETTE["bg"], foreground=PALETTE["muted"])
    style.configure("SurfaceMuted.TLabel", background=PALETTE["surface"], foreground=PALETTE["muted"])
    style.configure("HeroMuted.TLabel", background=PALETTE["surface_alt"], foreground=PALETTE["muted"])
    style.configure(
        "HeroTitle.TLabel",
        background=PALETTE["surface_alt"],
        foreground=PALETTE["accent"],
        font=("Microsoft YaHei UI", 28, "bold"),
    )
    style.configure(
        "Title.TLabel",
        background=PALETTE["bg"],
        foreground=PALETTE["text"],
        font=("Consolas", 16, "bold"),
    )
    style.configure(
        "Section.TLabel",
        background=PALETTE["bg"],
        foreground=PALETTE["accent"],
        font=("Consolas", 11, "bold"),
    )
    style.configure(
        "KpiValue.TLabel",
        background=PALETTE["surface"],
        foreground=PALETTE["accent"],
        font=("Consolas", 17, "bold"),
    )
    style.configure(
        "KpiCaption.TLabel",
        background=PALETTE["surface"],
        foreground=PALETTE["muted"],
        font=("Consolas", 9),
    )
    style.configure(
        "HudCode.TLabel",
        background=PALETTE["surface"],
        foreground=PALETTE["warn"],
        font=("Consolas", 8, "bold"),
    )
    style.configure(
        "HudRule.TLabel",
        background=PALETTE["bg"],
        foreground=PALETTE["border"],
        font=("Consolas", 8),
    )
    style.configure(
        "Badge.TLabel",
        background=PALETTE["surface_alt"],
        foreground=PALETTE["warn"],
        font=("Consolas", 9, "bold"),
        padding=(10, 4),
    )
    style.configure(
        "StatusIdle.TLabel",
        background=PALETTE["surface_soft"],
        foreground=PALETTE["muted"],
        font=("Consolas", 9, "bold"),
        padding=(10, 4),
    )
    style.configure(
        "StatusRunning.TLabel",
        background="#0b3842",
        foreground="#78e8ff",
        font=("Consolas", 9, "bold"),
        padding=(10, 4),
    )
    style.configure(
        "StatusWarn.TLabel",
        background="#3f2c10",
        foreground="#ffd57c",
        font=("Consolas", 9, "bold"),
        padding=(10, 4),
    )
    style.configure(
        "StatusError.TLabel",
        background="#3c1624",
        foreground="#ff9bb3",
        font=("Consolas", 9, "bold"),
        padding=(10, 4),
    )
    style.configure(
        "Emphasis.TLabel",
        background=PALETTE["surface"],
        foreground=PALETTE["accent"],
        font=("Consolas", 11, "bold"),
    )

    style.configure(
        "TLabelframe",
        background=PALETTE["surface"],
        borderwidth=1,
        relief="solid",
        bordercolor=PALETTE["border"],
    )
    style.configure(
        "TLabelframe.Label",
        background=PALETTE["surface"],
        foreground=PALETTE["accent"],
        font=("Consolas", 10, "bold"),
    )

    style.configure(
        "TEntry",
        fieldbackground=PALETTE["surface_soft"],
        foreground=PALETTE["text"],
        insertcolor=PALETTE["text"],
        bordercolor=PALETTE["border"],
        lightcolor=PALETTE["border"],
        darkcolor=PALETTE["border"],
        padding=(8, 7),
    )
    style.map(
        "TEntry",
        fieldbackground=[("readonly", PALETTE["surface_soft"])],
        foreground=[("readonly", PALETTE["text"])],
    )

    style.configure(
        "TCombobox",
        fieldbackground=PALETTE["surface_soft"],
        foreground=PALETTE["text"],
        arrowcolor=PALETTE["warn"],
        bordercolor=PALETTE["border"],
        lightcolor=PALETTE["border"],
        darkcolor=PALETTE["border"],
        padding=(8, 6),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", PALETTE["surface_soft"])],
        foreground=[("readonly", PALETTE["text"])],
    )

    style.configure(
        "TButton",
        background=PALETTE["surface_strong"],
        foreground=PALETTE["text"],
        borderwidth=0,
        focusthickness=0,
        padding=(18, 10),
        font=("Consolas", 10, "bold"),
    )
    style.map(
        "TButton",
        background=[("active", "#27435f"), ("pressed", "#27435f")],
        foreground=[("active", PALETTE["text"]), ("pressed", PALETTE["text"])],
    )
    style.configure(
        "Accent.TButton",
        background=PALETTE["accent"],
        foreground=PALETTE["accent_text"],
    )
    style.map(
        "Accent.TButton",
        background=[("active", PALETTE["accent_hover"]), ("pressed", PALETTE["accent_hover"])],
        foreground=[("active", PALETTE["accent_text"]), ("pressed", PALETTE["accent_text"])],
    )

    style.configure("TCheckbutton", background=PALETTE["bg"], foreground=PALETTE["text"])
    style.map(
        "TCheckbutton",
        foreground=[("active", PALETTE["text"])],
        background=[("active", PALETTE["bg"])],
    )
