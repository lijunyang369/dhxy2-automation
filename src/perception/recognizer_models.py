from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from PIL import Image

from src.domain import MatchResult


@dataclass(frozen=True)
class RecognitionSnapshot:
    matches: tuple[MatchResult, ...]
    named_regions: dict[str, tuple[int, int, int, int]] = field(default_factory=dict)
    region_images: dict[str, Image.Image] = field(default_factory=dict, repr=False)

    def has_region(self, region_name: str) -> bool:
        return region_name in self.named_regions

    def matching_templates(self, template_ids: tuple[str, ...]) -> tuple[MatchResult, ...]:
        template_id_set = set(template_ids)
        return tuple(match for match in self.matches if match.template_id in template_id_set)

    def region_image_for(self, region_name: str) -> Image.Image | None:
        return self.region_images.get(region_name)


@dataclass(frozen=True)
class RecognitionModuleSpec:
    module_id: str
    label: str
    region_name: str
    mode: str


@dataclass(frozen=True)
class RecognitionModuleResult:
    module_id: str
    label: str
    region_name: str
    mode: str
    detected: bool
    confidence: float
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
