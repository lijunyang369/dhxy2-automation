from __future__ import annotations

import unittest

import numpy as np
from PIL import Image

from src.perception import RecognitionSnapshot
from src.perception.round_recognition import (
    RoundDigitSegmenter,
    RoundRecognitionService,
    _build_digit_templates,
    _classify_digit_roi,
    _load_real_digit_templates,
)
from tests.smoke._paths import RESOURCES_ROOT, RUNS_ROOT


class RoundRecognitionServiceTestCase(unittest.TestCase):
    def test_service_returns_clear_reason_when_round_region_is_missing(self) -> None:
        result = RoundRecognitionService().recognize(RecognitionSnapshot(matches=(), named_regions={}))

        self.assertFalse(result.detected)
        self.assertIn("round region", result.reason)

    def test_service_recognizes_recent_live_round_sample_via_digit_band_fallback(self) -> None:
        sample_path = (
            RUNS_ROOT
            / "artifacts"
            / "probes"
            / "recognition-workbench"
            / "20260401T130432313997Z"
            / "region-round_number_region.png"
        )
        if not sample_path.is_file():
            self.skipTest("live round sample is not available in runs artifacts")

        result = RoundRecognitionService().recognize(
            RecognitionSnapshot(
                matches=(),
                named_regions={"round_number_region": (0, 100, 180, 150)},
                region_images={"round_number_region": Image.open(sample_path)},
            )
        )

        self.assertTrue(result.detected)
        self.assertEqual(1, result.round_number)
        self.assertGreaterEqual(result.overall_confidence, 0.7)


class RoundDigitRecognitionHelpersTestCase(unittest.TestCase):
    def test_segmenter_extracts_single_digit_component(self) -> None:
        mask = np.zeros((30, 22), dtype=np.uint8)
        mask[5:25, 6:15] = 255

        segments = RoundDigitSegmenter().segment(mask)

        self.assertEqual(1, len(segments))
        self.assertGreater(segments[0].area, 10)

    def test_segmenter_extracts_multiple_digit_components(self) -> None:
        mask = np.zeros((30, 48), dtype=np.uint8)
        mask[5:25, 4:13] = 255
        mask[5:25, 22:31] = 255

        segments = RoundDigitSegmenter().segment(mask)

        self.assertEqual(2, len(segments))
        self.assertLess(segments[0].bounds[0], segments[1].bounds[0])

    def test_real_digit_templates_cover_one_to_nine(self) -> None:
        templates = _load_real_digit_templates()

        self.assertEqual([str(index) for index in range(1, 10)], sorted(templates.keys()))

    def test_real_digit_templates_self_classify_as_expected(self) -> None:
        templates = _build_digit_templates()

        for digit in range(1, 10):
            image = np.array(
                Image.open(
                    RESOURCES_ROOT
                    / "templates"
                    / "battle"
                    / f"battle_round_digit_{digit}.png"
                ).convert("L")
            )
            recognized, confidence, _scores = _classify_digit_roi(image, templates)
            self.assertEqual(str(digit), recognized)
            self.assertGreaterEqual(confidence, 0.9)


if __name__ == "__main__":
    unittest.main()
