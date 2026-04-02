from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from src.domain import MatchResult
from src.perception import OpenCvTemplateMatcher, TemplateCatalog
from src.platform import FrameCapture, Rect


class OpenCvTemplateMatcherTestCase(unittest.TestCase):
    def test_match_finds_template_in_region(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            template_path = root / "template.png"
            catalog_path = root / "catalog.json"

            template = Image.new("RGB", (20, 20), color="black")
            draw = ImageDraw.Draw(template)
            draw.rectangle((4, 4, 15, 15), fill="white")
            template.save(template_path)

            frame = Image.new("RGB", (100, 100), color="black")
            frame.paste(template, (30, 40))
            capture = FrameCapture(image=frame)

            catalog_payload = {
                "templates": [
                    {
                        "id": "battle_ui",
                        "file": "template.png",
                        "scene": "battle",
                        "region": "battle_main",
                        "threshold": 0.95
                    }
                ]
            }
            catalog_path.write_text(json.dumps(catalog_payload), encoding="utf-8")

            matcher = OpenCvTemplateMatcher(TemplateCatalog.load(catalog_path))
            matches = matcher.match(capture, "battle_main")

            self.assertEqual(1, len(matches))
            self.assertEqual("battle_ui", matches[0].template_id)
            self.assertGreaterEqual(matches[0].confidence, 0.95)
            self.assertEqual((30, 40, 50, 60), matches[0].bounds)


if __name__ == "__main__":
    unittest.main()