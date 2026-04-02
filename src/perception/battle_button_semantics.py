from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.domain import BattleObservation


@dataclass(frozen=True)
class BattleButtonSemanticRule:
    button_ref: str
    label: str
    semantic_action: str
    verification_status: str
    before_any_of: tuple[str, ...] = ()
    after_any_of: tuple[str, ...] = ()
    after_none_of: tuple[str, ...] = ()
    notes: str | None = None


@dataclass(frozen=True)
class SemanticVerificationResult:
    button_ref: str
    confirmed: bool
    verification_status: str
    reason: str
    before_matches: tuple[str, ...]
    after_matches: tuple[str, ...]


class BattleButtonSemanticCatalog:
    def __init__(self, rules: dict[str, BattleButtonSemanticRule]) -> None:
        self._rules = rules

    @classmethod
    def load(cls, path: Path) -> "BattleButtonSemanticCatalog":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        rules: dict[str, BattleButtonSemanticRule] = {}
        for button_ref, rule_payload in payload.get("buttons", {}).items():
            rules[button_ref] = BattleButtonSemanticRule(
                button_ref=button_ref,
                label=str(rule_payload["label"]),
                semantic_action=str(rule_payload["semantic_action"]),
                verification_status=str(rule_payload.get("verification_status", "unknown")),
                before_any_of=tuple(str(item) for item in rule_payload.get("before_any_of", ())),
                after_any_of=tuple(str(item) for item in rule_payload.get("after_any_of", ())),
                after_none_of=tuple(str(item) for item in rule_payload.get("after_none_of", ())),
                notes=rule_payload.get("notes"),
            )
        return cls(rules)

    def get(self, button_ref: str) -> BattleButtonSemanticRule | None:
        return self._rules.get(button_ref)

    def verify(
        self,
        button_ref: str,
        before: BattleObservation,
        after: BattleObservation,
    ) -> SemanticVerificationResult:
        rule = self._rules.get(button_ref)
        before_matches = _sorted_template_ids(before)
        after_matches = _sorted_template_ids(after)

        if rule is None:
            return SemanticVerificationResult(
                button_ref=button_ref,
                confirmed=False,
                verification_status="missing_rule",
                reason="semantic rule is missing",
                before_matches=before_matches,
                after_matches=after_matches,
            )

        if rule.verification_status != "ready":
            return SemanticVerificationResult(
                button_ref=button_ref,
                confirmed=False,
                verification_status=rule.verification_status,
                reason=f"semantic verification is not ready: {rule.verification_status}",
                before_matches=before_matches,
                after_matches=after_matches,
            )

        if rule.before_any_of and not _has_any(before_matches, rule.before_any_of):
            return SemanticVerificationResult(
                button_ref=button_ref,
                confirmed=False,
                verification_status=rule.verification_status,
                reason="before-click semantic signal is missing",
                before_matches=before_matches,
                after_matches=after_matches,
            )

        if rule.after_any_of and not _has_any(after_matches, rule.after_any_of):
            return SemanticVerificationResult(
                button_ref=button_ref,
                confirmed=False,
                verification_status=rule.verification_status,
                reason="after-click semantic signal is missing",
                before_matches=before_matches,
                after_matches=after_matches,
            )

        if rule.after_none_of and _has_any(after_matches, rule.after_none_of):
            return SemanticVerificationResult(
                button_ref=button_ref,
                confirmed=False,
                verification_status=rule.verification_status,
                reason="after-click blocking signal is still present",
                before_matches=before_matches,
                after_matches=after_matches,
            )

        return SemanticVerificationResult(
            button_ref=button_ref,
            confirmed=True,
            verification_status=rule.verification_status,
            reason="semantic confirmation succeeded",
            before_matches=before_matches,
            after_matches=after_matches,
        )


def _sorted_template_ids(observation: BattleObservation) -> tuple[str, ...]:
    return tuple(sorted({match.template_id for match in observation.matches}))


def _has_any(matches: tuple[str, ...], expected: tuple[str, ...]) -> bool:
    current = set(matches)
    return any(item in current for item in expected)
