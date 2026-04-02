from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from src.domain import MatchResult
from src.perception.round_recognition import (
    _build_digit_templates,
    _classify_digit_roi,
    _load_real_digit_templates,
    build_round_digit_mask,
    build_round_digit_template,
    refresh_round_digit_template_cache,
)
from src.perception.template_catalog import TemplateCatalog
from src.platform import FrameCapture
from src.platform.models import Rect


@dataclass(frozen=True)
class RegionRequest:
    name: str
    rect: Rect | None = None
    use_template_match: bool = True


class NullTemplateMatcher:
    def match(self, frame: FrameCapture, region_name: str, rect: Rect | None = None) -> tuple[MatchResult, ...]:
        return ()


class StaticTemplateMatcher:
    def __init__(self, matches_by_region: dict[str, tuple[MatchResult, ...]]) -> None:
        self._matches_by_region = matches_by_region

    def match(self, frame: FrameCapture, region_name: str, rect: Rect | None = None) -> tuple[MatchResult, ...]:
        return self._matches_by_region.get(region_name, ())


class OpenCvTemplateMatcher:
    def __init__(self, catalog: TemplateCatalog) -> None:
        self._catalog = catalog

    def match(self, frame: FrameCapture, region_name: str, rect: Rect | None = None) -> tuple[MatchResult, ...]:
        frame_array = self._to_gray_array(frame.image, rect)
        offset_x = rect.left if rect is not None else 0
        offset_y = rect.top if rect is not None else 0
        matches: list[MatchResult] = []

        for definition in self._catalog.for_region(region_name):
            template = self._load_template(definition.file)
            if template.shape[0] > frame_array.shape[0] or template.shape[1] > frame_array.shape[1]:
                continue
            result = cv2.matchTemplate(frame_array, template, cv2.TM_CCOEFF_NORMED)
            _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
            if float(max_val) < definition.threshold:
                continue
            left, top = max_loc
            right = left + template.shape[1]
            bottom = top + template.shape[0]
            matches.append(
                MatchResult(
                    template_id=definition.id,
                    confidence=round(float(max_val), 4),
                    region_name=region_name,
                    bounds=(left + offset_x, top + offset_y, right + offset_x, bottom + offset_y),
                    note=definition.note,
                )
            )

        return tuple(matches)

    @staticmethod
    def _to_gray_array(image: Image.Image, rect: Rect | None) -> np.ndarray:
        if rect is not None:
            image = image.crop(rect.as_bbox())
        return cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2GRAY)

    @staticmethod
    @lru_cache(maxsize=128)
    def _load_template(path: Path) -> np.ndarray:
        image = Image.open(path).convert("RGB")
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)


__all__ = [
    "NullTemplateMatcher",
    "OpenCvTemplateMatcher",
    "RegionRequest",
    "StaticTemplateMatcher",
    "_build_digit_templates",
    "_classify_digit_roi",
    "_load_real_digit_templates",
    "build_round_digit_mask",
    "build_round_digit_template",
    "refresh_round_digit_template_cache",
]
