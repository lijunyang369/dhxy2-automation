from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowBinding:
    handle: int | None = None
    title: str | None = None
    class_name: str | None = None


@dataclass(frozen=True)
class AccountBinding:
    instance_id: str
    enabled: bool = True
    character_config_ref: str | None = None
    window: WindowBinding = WindowBinding()
