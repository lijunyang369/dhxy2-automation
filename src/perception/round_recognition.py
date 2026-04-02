from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.perception.recognizer_models import RecognitionSnapshot


@dataclass(frozen=True)
class RoundDigitSegment:
    bounds: tuple[int, int, int, int]
    area: int
    aspect_ratio: float
    image: np.ndarray = field(repr=False)


@dataclass(frozen=True)
class RoundDigitClassification:
    digit: str | None
    confidence: float
    candidate_scores: dict[str, float]
    bounds: tuple[int, int, int, int]


@dataclass(frozen=True)
class RoundRecognitionResult:
    detected: bool
    round_number: int | None
    region: tuple[int, int, int, int] | None
    locator_confidence: float
    image_quality_confidence: float
    digit_confidences: tuple[float, ...]
    overall_confidence: float
    sequence_confidence: float
    reason: str
    digits: tuple[str, ...] = ()
    digit_bounds: tuple[tuple[int, int, int, int], ...] = ()
    candidate_scores: tuple[dict[str, float], ...] = ()


@dataclass(frozen=True)
class RoundRegionLocation:
    found: bool
    region: tuple[int, int, int, int] | None
    image: Image.Image | None = field(default=None, repr=False)
    confidence: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class RoundPreprocessResult:
    roi: Image.Image
    mask: np.ndarray = field(repr=False)
    quality_confidence: float
    reason: str


class RoundRegionLocator:
    def __init__(self, region_name: str = "round_number_region") -> None:
        self._region_name = region_name

    @property
    def region_name(self) -> str:
        return self._region_name

    def locate(self, snapshot: RecognitionSnapshot) -> RoundRegionLocation:
        image = snapshot.region_image_for(self._region_name)
        region = snapshot.named_regions.get(self._region_name)
        if image is None or region is None:
            return RoundRegionLocation(
                found=False,
                region=None,
                confidence=0.0,
                reason=f"round region '{self._region_name}' is not configured",
            )
        return RoundRegionLocation(
            found=True,
            region=region,
            image=image,
            confidence=1.0,
            reason="configured_round_region",
        )


class RoundImagePreprocessor:
    def preprocess(self, roi: Image.Image) -> RoundPreprocessResult:
        mask = build_round_digit_mask(roi)
        active_pixels = int(np.count_nonzero(mask))
        total_pixels = int(mask.shape[0] * mask.shape[1]) or 1
        quality = round(min(1.0, active_pixels / max(1, total_pixels * 0.08)), 4)
        if active_pixels <= 0:
            return RoundPreprocessResult(
                roi=roi,
                mask=mask,
                quality_confidence=0.0,
                reason="no_digit_like_pixels_detected",
            )
        return RoundPreprocessResult(
            roi=roi,
            mask=mask,
            quality_confidence=quality,
            reason="digit_mask_ready",
        )


class RoundDigitSegmenter:
    def segment(self, mask: np.ndarray) -> tuple[RoundDigitSegment, ...]:
        height, width = mask.shape[:2]
        if height <= 0 or width <= 0 or not np.any(mask):
            return ()

        num_labels, labels, stats, _centroids = cv2.connectedComponentsWithStats(mask, connectivity=8)
        segments: list[RoundDigitSegment] = []
        min_area = max(10, int(height * width * 0.008))
        min_height = max(6, int(height * 0.22))
        min_width = max(3, int(width * 0.04))

        for label in range(1, num_labels):
            x, y, w, h, area = stats[label]
            if area < min_area or w < min_width or h < min_height:
                continue
            aspect_ratio = round(w / max(h, 1), 4)
            if aspect_ratio > 1.8:
                continue
            roi = mask[y : y + h, x : x + w]
            segments.append(
                RoundDigitSegment(
                    bounds=(x, y, x + w, y + h),
                    area=int(area),
                    aspect_ratio=aspect_ratio,
                    image=roi,
                )
            )

        segments.sort(key=lambda item: item.bounds[0])
        return tuple(segments)


class RoundDigitClassifier:
    def __init__(self) -> None:
        self._digit_templates = _build_digit_templates()

    @property
    def digit_templates(self) -> dict[str, tuple[np.ndarray, ...]]:
        return self._digit_templates

    def classify(self, segments: tuple[RoundDigitSegment, ...]) -> tuple[RoundDigitClassification, ...]:
        results: list[RoundDigitClassification] = []
        for segment in segments:
            digit, confidence, candidate_scores = _classify_digit_roi(segment.image, self._digit_templates)
            results.append(
                RoundDigitClassification(
                    digit=digit,
                    confidence=confidence,
                    candidate_scores=candidate_scores,
                    bounds=segment.bounds,
                )
            )
        return tuple(results)


class RoundNumberAssembler:
    def assemble(self, classifications: tuple[RoundDigitClassification, ...]) -> tuple[int | None, tuple[str, ...], float, str]:
        if not classifications:
            return None, (), 0.0, "no_digit_segments"

        digits: list[str] = []
        confidences: list[float] = []
        for entry in classifications:
            if entry.digit is None:
                return None, tuple(digits), 0.0, "digit_classification_failed"
            digits.append(entry.digit)
            confidences.append(entry.confidence)

        if not digits:
            return None, (), 0.0, "digit_classification_failed"

        text = "".join(digits)
        return int(text), tuple(digits), round(sum(confidences) / len(confidences), 4), "round_number_assembled"


class RoundSequenceTracker:
    def __init__(self) -> None:
        self._last_accepted_round: int | None = None

    def reset(self) -> None:
        self._last_accepted_round = None

    def apply(self, result: RoundRecognitionResult) -> RoundRecognitionResult:
        if not result.detected or result.round_number is None:
            return result

        current = result.round_number
        previous = self._last_accepted_round
        if previous is None:
            self._last_accepted_round = current
            return _replace_round_result(
                result,
                sequence_confidence=1.0,
                reason="accepted_first_round_observation",
            )

        if current == previous:
            return _replace_round_result(
                result,
                sequence_confidence=1.0,
                reason="accepted_same_round_observation",
            )

        if current == previous + 1:
            self._last_accepted_round = current
            return _replace_round_result(
                result,
                sequence_confidence=1.0,
                reason="accepted_next_round_observation",
            )

        if previous < current <= previous + 2:
            self._last_accepted_round = current
            return _replace_round_result(
                result,
                sequence_confidence=0.7,
                reason="accepted_round_jump_within_tolerance",
            )

        return RoundRecognitionResult(
            detected=False,
            round_number=None,
            region=result.region,
            locator_confidence=result.locator_confidence,
            image_quality_confidence=result.image_quality_confidence,
            digit_confidences=result.digit_confidences,
            overall_confidence=round(result.overall_confidence * 0.5, 4),
            sequence_confidence=0.0,
            reason=f"sequence_rejected(previous={previous}, current={current})",
            digits=result.digits,
            digit_bounds=result.digit_bounds,
            candidate_scores=result.candidate_scores,
        )


class RoundRecognitionService:
    def __init__(
        self,
        locator: RoundRegionLocator | None = None,
        preprocessor: RoundImagePreprocessor | None = None,
        segmenter: RoundDigitSegmenter | None = None,
        classifier: RoundDigitClassifier | None = None,
        assembler: RoundNumberAssembler | None = None,
        sequence_tracker: RoundSequenceTracker | None = None,
    ) -> None:
        self._locator = locator or RoundRegionLocator()
        self._preprocessor = preprocessor or RoundImagePreprocessor()
        self._segmenter = segmenter or RoundDigitSegmenter()
        self._classifier = classifier or RoundDigitClassifier()
        self._assembler = assembler or RoundNumberAssembler()
        self._sequence_tracker = sequence_tracker or RoundSequenceTracker()

    @property
    def region_name(self) -> str:
        return self._locator.region_name

    def recognize(self, snapshot: RecognitionSnapshot) -> RoundRecognitionResult:
        location = self._locator.locate(snapshot)
        if not location.found or location.image is None:
            return RoundRecognitionResult(
                detected=False,
                round_number=None,
                region=location.region,
                locator_confidence=location.confidence,
                image_quality_confidence=0.0,
                digit_confidences=(),
                overall_confidence=0.0,
                sequence_confidence=0.0,
                reason=location.reason,
            )

        processed = self._preprocessor.preprocess(location.image)
        if not np.any(processed.mask):
            return RoundRecognitionResult(
                detected=False,
                round_number=None,
                region=location.region,
                locator_confidence=location.confidence,
                image_quality_confidence=processed.quality_confidence,
                digit_confidences=(),
                overall_confidence=0.0,
                sequence_confidence=0.0,
                reason=processed.reason,
            )

        segments = self._segmenter.segment(processed.mask)
        classifications = self._classifier.classify(segments) if segments else ()
        round_number, digits, assembly_confidence, reason = self._assembler.assemble(classifications)
        if round_number is None:
            digit, band_confidence, band_bounds, band_candidate_scores = _match_digit_band(
                processed.mask,
                self._classifier.digit_templates,
            )
            if digit is not None:
                base_result = RoundRecognitionResult(
                    detected=True,
                    round_number=int(digit),
                    region=location.region,
                    locator_confidence=location.confidence,
                    image_quality_confidence=processed.quality_confidence,
                    digit_confidences=(band_confidence,),
                    overall_confidence=round(
                        (location.confidence + processed.quality_confidence + band_confidence) / 3,
                        4,
                    ),
                    sequence_confidence=1.0,
                    reason="round_number_recognized_from_digit_band",
                    digits=(digit,),
                    digit_bounds=(band_bounds,) if band_bounds is not None else (),
                    candidate_scores=(band_candidate_scores,),
                )
                return self._sequence_tracker.apply(base_result)

            failure_reason = "digit_segmentation_failed" if not segments else reason
            return RoundRecognitionResult(
                detected=False,
                round_number=None,
                region=location.region,
                locator_confidence=location.confidence,
                image_quality_confidence=processed.quality_confidence,
                digit_confidences=tuple(entry.confidence for entry in classifications),
                overall_confidence=0.0,
                sequence_confidence=0.0,
                reason=failure_reason,
                digits=digits,
                digit_bounds=tuple(entry.bounds for entry in classifications),
                candidate_scores=tuple(entry.candidate_scores for entry in classifications),
            )

        base_result = RoundRecognitionResult(
            detected=True,
            round_number=round_number,
            region=location.region,
            locator_confidence=location.confidence,
            image_quality_confidence=processed.quality_confidence,
            digit_confidences=tuple(entry.confidence for entry in classifications),
            overall_confidence=round(
                (location.confidence + processed.quality_confidence + assembly_confidence) / 3,
                4,
            ),
            sequence_confidence=1.0,
            reason=reason,
            digits=digits,
            digit_bounds=tuple(entry.bounds for entry in classifications),
            candidate_scores=tuple(entry.candidate_scores for entry in classifications),
        )
        return self._sequence_tracker.apply(base_result)


def build_round_digit_mask(image: Image.Image) -> np.ndarray:
    rgb = np.array(image.convert("RGB"))
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

    lower = np.array([10, 80, 120], dtype=np.uint8)
    upper = np.array([40, 255, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.medianBlur(mask, 3)
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    if np.any(mask):
        return mask

    # Fallback for saved binary templates or grayscale captures used by tests.
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    threshold_mode = cv2.THRESH_BINARY_INV if float(gray.mean()) > 127 else cv2.THRESH_BINARY
    _, binary = cv2.threshold(gray, 60, 255, threshold_mode)
    return binary


def build_round_digit_template(image: Image.Image) -> np.ndarray | None:
    mask = build_round_digit_mask(image)
    segments = RoundDigitSegmenter().segment(mask)
    if not segments:
        return None
    segment = max(segments, key=lambda entry: entry.area)
    return cv2.resize(segment.image, (22, 30), interpolation=cv2.INTER_NEAREST)


def refresh_round_digit_template_cache() -> None:
    _build_digit_templates.cache_clear()


def _classify_digit_roi(
    roi: np.ndarray,
    templates: dict[str, tuple[np.ndarray, ...]],
) -> tuple[str | None, float, dict[str, float]]:
    normalized = cv2.resize(roi, (22, 30), interpolation=cv2.INTER_NEAREST)
    best_digit: str | None = None
    best_score = -1.0
    candidate_scores: dict[str, float] = {}

    for digit, variants in templates.items():
        digit_best = -1.0
        for variant in variants:
            result = cv2.matchTemplate(normalized, variant, cv2.TM_CCOEFF_NORMED)
            score = float(result[0][0])
            digit_best = max(digit_best, score)
            if score > best_score:
                best_score = score
                best_digit = digit
        candidate_scores[digit] = round(digit_best, 4)

    if best_score < 0.35:
        return None, round(best_score, 4), candidate_scores
    return best_digit, round(best_score, 4), candidate_scores


def _match_digit_band(
    mask: np.ndarray,
    templates: dict[str, tuple[np.ndarray, ...]],
) -> tuple[str | None, float, tuple[int, int, int, int] | None, dict[str, float]]:
    band, band_bounds = _extract_digit_band(mask)
    if band is None or band_bounds is None:
        return None, 0.0, None, {}

    enlarged = cv2.resize(
        band,
        (max(1, band.shape[1] * 2), max(1, band.shape[0] * 2)),
        interpolation=cv2.INTER_NEAREST,
    )

    best_digit: str | None = None
    best_score = -1.0
    best_loc: tuple[int, int] | None = None
    best_shape: tuple[int, int] | None = None
    candidate_scores: dict[str, float] = {}

    for digit, variants in templates.items():
        digit_best = -1.0
        for variant in variants:
            if variant.shape[0] > enlarged.shape[0] or variant.shape[1] > enlarged.shape[1]:
                continue
            result = cv2.matchTemplate(enlarged, variant, cv2.TM_CCOEFF_NORMED)
            _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)
            score = float(max_val)
            if score > digit_best:
                digit_best = score
            if score > best_score:
                best_digit = digit
                best_score = score
                best_loc = max_loc
                best_shape = variant.shape
        candidate_scores[digit] = round(digit_best, 4)

    if best_digit is None or best_loc is None or best_shape is None or best_score < 0.45:
        return None, round(best_score, 4), band_bounds, candidate_scores

    band_left, band_top, _band_right, _band_bottom = band_bounds
    left = band_left + int(best_loc[0] / 2)
    top = band_top + int(best_loc[1] / 2)
    right = left + max(1, int(best_shape[1] / 2))
    bottom = top + max(1, int(best_shape[0] / 2))
    return best_digit, round(best_score, 4), (left, top, right, bottom), candidate_scores


def _extract_digit_band(mask: np.ndarray) -> tuple[np.ndarray | None, tuple[int, int, int, int] | None]:
    _height, width = mask.shape[:2]
    left = max(0, int(width * 0.2))
    right = min(width, int(width * 0.42))
    if right <= left:
        return None, None

    band = mask[:, left:right]
    if not np.any(band):
        return None, None

    points = cv2.findNonZero(band)
    if points is None:
        return None, None
    x, y, w, h = cv2.boundingRect(points)
    if w <= 0 or h <= 0:
        return None, None
    return band[y : y + h, x : x + w], (left + x, y, left + x + w, y + h)


def _replace_round_result(
    result: RoundRecognitionResult,
    *,
    sequence_confidence: float,
    reason: str,
) -> RoundRecognitionResult:
    return RoundRecognitionResult(
        detected=result.detected,
        round_number=result.round_number,
        region=result.region,
        locator_confidence=result.locator_confidence,
        image_quality_confidence=result.image_quality_confidence,
        digit_confidences=result.digit_confidences,
        overall_confidence=result.overall_confidence,
        sequence_confidence=sequence_confidence,
        reason=reason,
        digits=result.digits,
        digit_bounds=result.digit_bounds,
        candidate_scores=result.candidate_scores,
    )


@lru_cache(maxsize=1)
def _build_digit_templates() -> dict[str, tuple[np.ndarray, ...]]:
    fonts = _resolve_digit_fonts()
    templates: dict[str, list[np.ndarray]] = {str(index): [] for index in range(10)}
    real_templates = _load_real_digit_templates()
    for digit, template in real_templates.items():
        templates[digit].append(template)
    for digit in templates:
        if digit in real_templates:
            continue
        for font in fonts:
            canvas = Image.new("RGB", (28, 36), "black")
            draw = ImageDraw.Draw(canvas)
            draw.text(
                (4, 0),
                digit,
                font=font,
                fill=(255, 210, 80),
                stroke_width=2,
                stroke_fill=(45, 25, 0),
            )
            gray = cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2GRAY)
            _, binary = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY)
            templates[digit].append(cv2.resize(binary, (22, 30), interpolation=cv2.INTER_NEAREST))
    return {digit: tuple(items) for digit, items in templates.items()}


def _load_real_digit_templates() -> dict[str, np.ndarray]:
    base_dir = Path(__file__).resolve().parents[2] / "resources" / "templates" / "battle"
    templates: dict[str, np.ndarray] = {}
    for digit in range(10):
        path = base_dir / f"battle_round_digit_{digit}.png"
        if not path.is_file():
            continue
        image = Image.open(path).convert("L")
        array = np.array(image)
        _, binary = cv2.threshold(array, 60, 255, cv2.THRESH_BINARY)
        templates[str(digit)] = cv2.resize(binary, (22, 30), interpolation=cv2.INTER_NEAREST)
    return templates


def _resolve_digit_fonts() -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ...]:
    candidates = [
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "msyhbd.ttc",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "msyh.ttc",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "simhei.ttf",
        Path(os.environ.get("WINDIR", "C:\\Windows")) / "Fonts" / "arialbd.ttf",
    ]
    fonts: list[ImageFont.FreeTypeFont | ImageFont.ImageFont] = []
    for path in candidates:
        if not path.is_file():
            continue
        try:
            fonts.append(ImageFont.truetype(str(path), 26))
        except OSError:
            continue
    if not fonts:
        fonts.append(ImageFont.load_default())
    return tuple(fonts)
