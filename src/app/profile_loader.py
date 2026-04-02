from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.app.config_refs import configs_root, resolve_config_reference
from src.domain import (
    CharacterKnowledgeRefs,
    CharacterProfile,
    CharacterSystemKnowledge,
    KnowledgeSource,
    PetSystemKnowledge,
    ValidationRule,
)


class CharacterProfileLoader:
    def load(self, path: Path) -> CharacterProfile:
        resolved_path = Path(path).resolve()
        payload = json.loads(resolved_path.read_text(encoding="utf-8-sig"))
        knowledge_refs = CharacterKnowledgeRefs(
            character_system=payload.get("knowledge_refs", {}).get("character_system"),
            pet_system=payload.get("knowledge_refs", {}).get("pet_system"),
        )
        return CharacterProfile(
            character_id=str(payload["character_id"]),
            role_type=str(payload["role_type"]),
            skill_set=tuple(str(item) for item in payload.get("skill_set", ())),
            default_target_rule=str(payload["default_target_rule"]),
            knowledge_refs=knowledge_refs,
            character_system=self._load_character_system(resolved_path, knowledge_refs.character_system),
            pet_system=self._load_pet_system(resolved_path, knowledge_refs.pet_system),
        )

    def _load_character_system(
        self,
        base_path: Path,
        relative_ref: str | None,
    ) -> CharacterSystemKnowledge | None:
        if not relative_ref:
            return None
        payload = self._load_json(base_path, relative_ref)
        return CharacterSystemKnowledge(
            domain=str(payload["domain"]),
            source=self._load_sources(payload.get("source", ())),
            base_attributes=tuple(str(item) for item in payload.get("base_attributes", ())),
            derived_attributes=tuple(str(item) for item in payload.get("derived_attributes", ())),
            resistance_caps=dict(payload.get("resistance_caps", {})),
            rebirth_effects=tuple(str(item) for item in payload.get("rebirth_effects", ())),
        )

    def _load_pet_system(
        self,
        base_path: Path,
        relative_ref: str | None,
    ) -> PetSystemKnowledge | None:
        if not relative_ref:
            return None
        payload = self._load_json(base_path, relative_ref)
        rules = tuple(
            ValidationRule(
                rule_id=str(item["rule_id"]),
                description=str(item["description"]),
                status=str(item["status"]),
                details=dict(item.get("details", {})),
            )
            for item in payload.get("validation_rules", ())
        )
        return PetSystemKnowledge(
            domain=str(payload["domain"]),
            source=self._load_sources(payload.get("source", ())),
            core_fields=tuple(str(item) for item in payload.get("core_fields", ())),
            base_formula_inputs=tuple(str(item) for item in payload.get("base_formula_inputs", ())),
            validation_rules=rules,
        )

    def _load_sources(self, raw_sources: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> tuple[KnowledgeSource, ...]:
        return tuple(
            KnowledgeSource(
                page=str(item["page"]),
                url=str(item["url"]),
                updated_at=str(item["updated_at"]),
            )
            for item in raw_sources
        )

    def _load_json(self, base_path: Path, relative_ref: str) -> dict[str, Any]:
        knowledge_root = configs_root(base_path) / "knowledge"
        resolved = resolve_config_reference(base_path, relative_ref, allowed_root=knowledge_root)
        return json.loads(resolved.read_text(encoding="utf-8-sig"))
