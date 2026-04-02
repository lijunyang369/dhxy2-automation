from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class KnowledgeSource:
    page: str
    url: str
    updated_at: str


@dataclass(frozen=True)
class ValidationRule:
    rule_id: str
    description: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CharacterSystemKnowledge:
    domain: str
    source: tuple[KnowledgeSource, ...]
    base_attributes: tuple[str, ...]
    derived_attributes: tuple[str, ...]
    resistance_caps: dict[str, Any]
    rebirth_effects: tuple[str, ...]


@dataclass(frozen=True)
class PetSystemKnowledge:
    domain: str
    source: tuple[KnowledgeSource, ...]
    core_fields: tuple[str, ...]
    base_formula_inputs: tuple[str, ...]
    validation_rules: tuple[ValidationRule, ...]


@dataclass(frozen=True)
class CharacterKnowledgeRefs:
    character_system: str | None = None
    pet_system: str | None = None


@dataclass(frozen=True)
class CharacterProfile:
    character_id: str
    role_type: str
    skill_set: tuple[str, ...]
    default_target_rule: str
    knowledge_refs: CharacterKnowledgeRefs = field(default_factory=CharacterKnowledgeRefs)
    character_system: CharacterSystemKnowledge | None = None
    pet_system: PetSystemKnowledge | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
