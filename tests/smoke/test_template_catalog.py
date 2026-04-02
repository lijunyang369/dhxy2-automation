from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.perception import TemplateCatalog


class TemplateCatalogTestCase(unittest.TestCase):
    def test_missing_files_reports_absent_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            catalog_path = root / "catalog.json"
            catalog_payload = {
                "templates": [
                    {
                        "id": "battle_ui",
                        "file": "present.png",
                        "scene": "battle",
                        "region": "battle_auto_button"
                    },
                    {
                        "id": "battle_skill_bar",
                        "file": "missing.png",
                        "scene": "battle",
                        "region": "skill_bar"
                    }
                ]
            }
            (root / "present.png").write_bytes(b"png")
            catalog_path.write_text(json.dumps(catalog_payload), encoding="utf-8")

            catalog = TemplateCatalog.load(catalog_path)
            missing_files = catalog.missing_files()

            self.assertEqual(1, len(missing_files))
            self.assertEqual((root / "missing.png").resolve(), missing_files[0])


if __name__ == "__main__":
    unittest.main()
