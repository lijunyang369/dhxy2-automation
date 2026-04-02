from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

from src.platform import FrameCapture, Rect


@dataclass(frozen=True)
class RegionSpec:
    name: str
    rect: Rect
    enabled: bool = True


class RegionCropper:
    def crop(self, frame: FrameCapture, region: RegionSpec) -> Image.Image:
        if not region.enabled:
            raise ValueError(f"region {region.name} is disabled")
        return frame.image.crop(region.rect.as_bbox())
