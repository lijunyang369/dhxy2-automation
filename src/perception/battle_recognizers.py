from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from src.domain import MatchResult
from src.perception.ocr_client import OCRServiceClient
from src.perception.ocr_profiles import ocr_profile_for_module
from src.perception.recognizer_models import (
    RecognitionModuleResult,
    RecognitionModuleSpec,
    RecognitionSnapshot,
)


class RecognitionModule(Protocol):
    @property
    def spec(self) -> RecognitionModuleSpec: ...

    def recognize(self, snapshot: RecognitionSnapshot) -> RecognitionModuleResult: ...


def _default_details(snapshot: RecognitionSnapshot, spec: RecognitionModuleSpec) -> dict[str, object]:
    return {
        "region_configured": snapshot.has_region(spec.region_name),
        "region_name": spec.region_name,
        "mode": spec.mode,
    }


def _best_region_match(
    snapshot: RecognitionSnapshot,
    region_name: str,
    template_ids: tuple[str, ...],
) -> MatchResult | None:
    candidates = [
        match
        for match in snapshot.matching_templates(template_ids)
        if match.region_name == region_name
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item.confidence)


@dataclass(frozen=True)
class TemplatePresenceRecognizer:
    spec: RecognitionModuleSpec
    template_ids: tuple[str, ...]

    def recognize(self, snapshot: RecognitionSnapshot) -> RecognitionModuleResult:
        details = _default_details(snapshot, self.spec)
        details["template_ids"] = list(self.template_ids)
        if not snapshot.has_region(self.spec.region_name):
            return RecognitionModuleResult(
                module_id=self.spec.module_id,
                label=self.spec.label,
                region_name=self.spec.region_name,
                mode=self.spec.mode,
                detected=False,
                confidence=0.0,
                summary="场景未配置该识别区域",
                details=details,
            )

        best_match = _best_region_match(snapshot, self.spec.region_name, self.template_ids)
        if best_match is None:
            details["matched_templates"] = []
            return RecognitionModuleResult(
                module_id=self.spec.module_id,
                label=self.spec.label,
                region_name=self.spec.region_name,
                mode=self.spec.mode,
                detected=False,
                confidence=0.0,
                summary=f"未命中模板: {', '.join(self.template_ids)}",
                details=details,
            )

        details["matched_templates"] = [best_match.template_id]
        details["bounds"] = list(best_match.bounds) if best_match.bounds else None
        details["note"] = best_match.note
        return RecognitionModuleResult(
            module_id=self.spec.module_id,
            label=self.spec.label,
            region_name=self.spec.region_name,
            mode=self.spec.mode,
            detected=True,
            confidence=best_match.confidence,
            summary=f"命中模板: {best_match.template_id}",
            details=details,
        )


class BattleRoundRecognizer:
    def __init__(self, spec: RecognitionModuleSpec, ocr_client: OCRServiceClient | None = None) -> None:
        self.spec = spec
        self._ocr_client = ocr_client

    def recognize(self, snapshot: RecognitionSnapshot) -> RecognitionModuleResult:
        details = _default_details(snapshot, self.spec)
        region = snapshot.named_regions.get(self.spec.region_name)
        region_image = snapshot.region_image_for(self.spec.region_name)
        details["region"] = list(region) if region is not None else None

        if region is None or region_image is None:
            return RecognitionModuleResult(
                module_id=self.spec.module_id,
                label=self.spec.label,
                region_name=self.spec.region_name,
                mode=self.spec.mode,
                detected=False,
                confidence=0.0,
                summary="未识别到回合数: round region is not configured",
                details=details,
            )

        if self._ocr_client is None:
            details["reason"] = "ocr_service_disabled"
            return RecognitionModuleResult(
                module_id=self.spec.module_id,
                label=self.spec.label,
                region_name=self.spec.region_name,
                mode=self.spec.mode,
                detected=False,
                confidence=0.0,
                summary="未识别到回合数: ocr_service_disabled",
                details=details,
            )

        profile = ocr_profile_for_module(self.spec.module_id)
        ocr_result = self._ocr_client.read_text_from_image(
            region_image,
            allowlist=profile.allowlist if profile is not None else None,
        )
        details["ocr"] = ocr_result.to_dict()
        if not ocr_result.ok:
            details["reason"] = ocr_result.error_code or "ocr_failed"
            return RecognitionModuleResult(
                module_id=self.spec.module_id,
                label=self.spec.label,
                region_name=self.spec.region_name,
                mode=self.spec.mode,
                detected=False,
                confidence=0.0,
                summary=f"未识别到回合数: {details['reason']}",
                details=details,
            )

        text = ocr_result.text.strip()
        round_number, digits, parse_reason = _parse_round_text(text)
        details["ocr_text"] = text
        details["round_number"] = round_number
        details["digits"] = list(digits)
        details["overall_confidence"] = ocr_result.confidence
        details["reason"] = parse_reason

        if round_number is None:
            return RecognitionModuleResult(
                module_id=self.spec.module_id,
                label=self.spec.label,
                region_name=self.spec.region_name,
                mode=self.spec.mode,
                detected=False,
                confidence=ocr_result.confidence,
                summary=f"未识别到回合数: {parse_reason}",
                details=details,
            )

        return RecognitionModuleResult(
            module_id=self.spec.module_id,
            label=self.spec.label,
            region_name=self.spec.region_name,
            mode=self.spec.mode,
            detected=True,
            confidence=ocr_result.confidence,
            summary=f"识别到第 {round_number} 回合",
            details=details,
        )


def build_default_battle_recognizers(ocr_client: OCRServiceClient | None = None) -> tuple[RecognitionModule, ...]:
    return (
        TemplatePresenceRecognizer(
            spec=RecognitionModuleSpec(
                module_id="battle_scene",
                label="战斗场景识别",
                region_name="battle_auto_button",
                mode="template",
            ),
            template_ids=("battle_ui",),
        ),
        BattleRoundRecognizer(
            spec=RecognitionModuleSpec(
                module_id="battle_round",
                label="战斗回合识别",
                region_name="round_number_region",
                mode="round_recognition",
            ),
            ocr_client=ocr_client,
        ),
        TemplatePresenceRecognizer(
            spec=RecognitionModuleSpec(
                module_id="battle_action_prompt",
                label="战斗指令提示识别",
                region_name="battle_prompt",
                mode="template",
            ),
            template_ids=("battle_action_prompt",),
        ),
        TemplatePresenceRecognizer(
            spec=RecognitionModuleSpec(
                module_id="battle_skill_bar",
                label="战斗技能栏识别",
                region_name="skill_bar",
                mode="template",
            ),
            template_ids=("battle_skill_bar",),
        ),
        TemplatePresenceRecognizer(
            spec=RecognitionModuleSpec(
                module_id="battle_target_select",
                label="目标选择识别",
                region_name="target_panel",
                mode="template",
            ),
            template_ids=("battle_target_panel",),
        ),
        TemplatePresenceRecognizer(
            spec=RecognitionModuleSpec(
                module_id="battle_settlement",
                label="战斗结算识别",
                region_name="settlement_panel",
                mode="template",
            ),
            template_ids=("battle_settlement",),
        ),
    )


class BattleRecognitionSuite:
    def __init__(
        self,
        modules: tuple[RecognitionModule, ...] | None = None,
        *,
        ocr_client: OCRServiceClient | None = None,
    ) -> None:
        self._modules = modules or build_default_battle_recognizers(ocr_client=ocr_client)

    @property
    def specs(self) -> tuple[RecognitionModuleSpec, ...]:
        return tuple(module.spec for module in self._modules)

    def evaluate(self, snapshot: RecognitionSnapshot) -> dict[str, RecognitionModuleResult]:
        return {
            module.spec.module_id: module.recognize(snapshot)
            for module in self._modules
        }


_ROUND_TEXT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "round_text_matched_full_pattern",
        re.compile(r"\u7b2c\s*(\d{1,2})\s*\u56de\s*\u5408"),
    ),
    (
        "round_text_matched_missing_suffix",
        re.compile(r"\u7b2c\s*(\d{1,2})\s*\u56de"),
    ),
    (
        "round_text_matched_missing_prefix",
        re.compile(r"(?<!\d)(\d{1,2})\s*\u56de\s*\u5408"),
    ),
)


def _normalize_round_text(text: str) -> str:
    return re.sub(r"[\s:：,，;；|/\\\-_]+", "", text)


def _parse_round_text(text: str) -> tuple[int | None, tuple[str, ...], str]:
    normalized = _normalize_round_text(text)
    for reason, pattern in _ROUND_TEXT_PATTERNS:
        matched = pattern.search(normalized)
        if matched is None:
            continue
        digits = matched.group(1)
        return int(digits), tuple(digits), reason
    return None, (), "ocr_text_has_no_structured_round"
