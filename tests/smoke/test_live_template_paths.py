from __future__ import annotations

import unittest

from PIL import Image

from src.perception import OpenCvTemplateMatcher, TemplateCatalog
from src.platform import FrameCapture
from tests.smoke._paths import RESOURCES_ROOT, RUNS_ROOT


class LiveTemplatePathTestCase(unittest.TestCase):
    def test_catalog_templates_match_manual_battle_capture(self) -> None:
        catalog = TemplateCatalog.load(RESOURCES_ROOT / "templates" / "battle" / "catalog.json")
        matcher = OpenCvTemplateMatcher(catalog)
        frame = FrameCapture(image=Image.open(RUNS_ROOT / "artifacts" / "battle-capture-focused.png"))

        main_matches = matcher.match(frame, "battle_auto_button")
        prompt_matches = matcher.match(frame, "battle_prompt")
        skill_matches = matcher.match(frame, "skill_bar")

        self.assertTrue(any(match.template_id == "battle_ui" for match in main_matches))
        self.assertTrue(any(match.template_id == "battle_action_prompt" for match in prompt_matches))
        self.assertTrue(any(match.template_id == "battle_skill_bar" for match in skill_matches))


if __name__ == "__main__":
    unittest.main()
