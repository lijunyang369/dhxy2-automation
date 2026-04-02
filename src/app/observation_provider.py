from __future__ import annotations

from dataclasses import dataclass

from src.app.interfaces import ObservationProvider
from src.domain import BattleObservation, MatchResult
from src.perception import ObservationBuilder, RecognitionSnapshot
from src.perception.interfaces import TemplateMatcher
from src.perception.services import RegionRequest
from src.platform import FrameCapture, WindowInfo, WindowSession
from src.platform.models import Rect


@dataclass(frozen=True)
class DefaultObservationProviderConfig:
    regions: tuple[RegionRequest, ...]


@dataclass(frozen=True)
class ObservationCapture:
    frame: FrameCapture
    window_info: WindowInfo
    snapshot: RecognitionSnapshot
    named_regions: dict[str, Rect]


class DefaultObservationProvider(ObservationProvider):
    def __init__(
        self,
        template_matcher: TemplateMatcher,
        builder: ObservationBuilder | None = None,
        config: DefaultObservationProviderConfig | None = None,
    ) -> None:
        self._template_matcher = template_matcher
        self._builder = builder or ObservationBuilder()
        self._config = config or DefaultObservationProviderConfig(regions=())

    @property
    def builder(self) -> ObservationBuilder:
        return self._builder

    def capture(self, window_session: WindowSession) -> ObservationCapture:
        window_info = window_session.snapshot()
        frame = window_session.capture_client()

        matches: list[MatchResult] = []
        named_regions: dict[str, Rect] = {}
        region_images: dict[str, object] = {}

        for region in self._config.regions:
            if region.rect is not None:
                named_regions[region.name] = region.rect
                region_images[region.name] = frame.image.crop(region.rect.as_bbox())
            if region.use_template_match:
                matches.extend(self._template_matcher.match(frame, region.name, region.rect))
        snapshot = self._builder.build_snapshot(
            matches=tuple(matches),
            named_regions=named_regions,
            region_images=region_images,
        )
        return ObservationCapture(
            frame=frame,
            window_info=window_info,
            snapshot=snapshot,
            named_regions=named_regions,
        )

    def observe(self, window_session: WindowSession) -> BattleObservation:
        capture = self.capture(window_session)
        return self._builder.build_from_snapshot(
            frame=capture.frame,
            window_info=capture.window_info,
            snapshot=capture.snapshot,
        )
