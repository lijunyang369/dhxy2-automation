from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OCRModuleProfile:
    module_id: str
    mode: str
    allowlist: str | None = None


_DEFAULT_OCR_PROFILES: dict[str, OCRModuleProfile] = {
    "battle_round": OCRModuleProfile(
        module_id="battle_round",
        mode="text",
        allowlist="0123456789第回合",
    ),
    "battle_action_prompt": OCRModuleProfile(
        module_id="battle_action_prompt",
        mode="lines",
    ),
    "battle_target_select": OCRModuleProfile(
        module_id="battle_target_select",
        mode="lines",
    ),
    "battle_settlement": OCRModuleProfile(
        module_id="battle_settlement",
        mode="lines",
    ),
}


def ocr_profile_for_module(module_id: str) -> OCRModuleProfile | None:
    return _DEFAULT_OCR_PROFILES.get(module_id)
