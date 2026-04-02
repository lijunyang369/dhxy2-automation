from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.app import CharacterProfileLoader
from tests.smoke._paths import CONFIGS_ROOT


class CharacterProfileLoaderTestCase(unittest.TestCase):
    def test_loads_profile_and_referenced_knowledge_configs(self) -> None:
        loader = CharacterProfileLoader()

        profile = loader.load(CONFIGS_ROOT / "characters" / "mage-default.json")

        self.assertEqual("mage-default", profile.character_id)
        self.assertEqual("mage", profile.role_type)
        self.assertIsNotNone(profile.character_system)
        self.assertIsNotNone(profile.pet_system)
        self.assertIn("growth_rate", profile.pet_system.core_fields)
        self.assertEqual("2014-07-29 06:12:50", profile.character_system.source[0].updated_at)

    def test_rejects_knowledge_refs_outside_configs_knowledge_root(self) -> None:
        loader = CharacterProfileLoader()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            character_config = temp_root / "configs" / "characters" / "temp-character.json"
            outside_knowledge = temp_root / "outside-knowledge.json"

            character_config.parent.mkdir(parents=True, exist_ok=True)
            outside_knowledge.write_text(
                json.dumps(
                    {
                        "domain": "outside",
                        "source": [],
                        "base_attributes": [],
                        "derived_attributes": [],
                        "resistance_caps": {},
                        "rebirth_effects": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            character_config.write_text(
                json.dumps(
                    {
                        "character_id": "temp-character",
                        "role_type": "mage",
                        "skill_set": [],
                        "default_target_rule": "enemy_front",
                        "knowledge_refs": {
                            "character_system": "../../outside-knowledge.json",
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "escapes allowed root"):
                loader.load(character_config)


if __name__ == "__main__":
    unittest.main()
