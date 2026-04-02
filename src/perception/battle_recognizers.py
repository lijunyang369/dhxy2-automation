from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain import MatchResult
from src.perception.recognizer_models import (
    RecognitionModuleResult,
    RecognitionModuleSpec,
    RecognitionSnapshot,
)
from src.perception.round_recognition import RoundRecognitionService


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
    def __init__(self, spec: RecognitionModuleSpec, service: RoundRecognitionService | None = None) -> None:
        self.spec = spec
        self._service = service or RoundRecognitionService()

    def recognize(self, snapshot: RecognitionSnapshot) -> RecognitionModuleResult:
        details = _default_details(snapshot, self.spec)
        result = self._service.recognize(snapshot)
        details.update(
            {
                "round_number": result.round_number,
                "digits": list(result.digits),
                "reason": result.reason,
                "region": list(result.region) if result.region else None,
                "locator_confidence": result.locator_confidence,
                "image_quality_confidence": result.image_quality_confidence,
                "digit_confidences": list(result.digit_confidences),
                "overall_confidence": result.overall_confidence,
                "sequence_confidence": result.sequence_confidence,
                "digit_bounds": [list(bounds) for bounds in result.digit_bounds],
                "candidate_scores": list(result.candidate_scores),
            }
        )
        if not result.detected or result.round_number is None:
            return RecognitionModuleResult(
                module_id=self.spec.module_id,
                label=self.spec.label,
                region_name=self.spec.region_name,
                mode=self.spec.mode,
                detected=False,
                confidence=result.overall_confidence,
                summary=f"未识别到回合数: {result.reason}",
                details=details,
            )

        return RecognitionModuleResult(
            module_id=self.spec.module_id,
            label=self.spec.label,
            region_name=self.spec.region_name,
            mode=self.spec.mode,
            detected=True,
            confidence=result.overall_confidence,
            summary=f"识别到第 {result.round_number} 回合",
            details=details,
        )


def build_default_battle_recognizers() -> tuple[RecognitionModule, ...]:
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
            )
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
    def __init__(self, modules: tuple[RecognitionModule, ...] | None = None) -> None:
        self._modules = modules or build_default_battle_recognizers()

    @property
    def specs(self) -> tuple[RecognitionModuleSpec, ...]:
        return tuple(module.spec for module in self._modules)

    def evaluate(self, snapshot: RecognitionSnapshot) -> dict[str, RecognitionModuleResult]:
        return {
            module.spec.module_id: module.recognize(snapshot)
            for module in self._modules
        }
