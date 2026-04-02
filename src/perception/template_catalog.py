from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TemplateDefinition:
    id: str
    file: Path
    scene: str
    region: str
    threshold: float = 0.9
    resolution: str | None = None
    anchor: str | None = None
    note: str | None = None


class TemplateCatalog:
    def __init__(self, templates: tuple[TemplateDefinition, ...]) -> None:
        self._templates = templates

    @classmethod
    def load(cls, path: Path) -> "TemplateCatalog":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        base_dir = path.parent
        templates = tuple(
            TemplateDefinition(
                id=entry["id"],
                file=(base_dir / entry["file"]).resolve(),
                scene=entry.get("scene", "battle"),
                region=entry["region"],
                threshold=float(entry.get("threshold", 0.9)),
                resolution=entry.get("resolution"),
                anchor=entry.get("anchor"),
                note=entry.get("note"),
            )
            for entry in payload.get("templates", [])
        )
        return cls(templates)

    def for_region(self, region_name: str) -> tuple[TemplateDefinition, ...]:
        return tuple(template for template in self._templates if template.region == region_name)

    def all(self) -> tuple[TemplateDefinition, ...]:
        return self._templates

    def missing_files(self) -> tuple[Path, ...]:
        return tuple(template.file for template in self._templates if not template.file.exists())

    def is_empty(self) -> bool:
        return not self._templates