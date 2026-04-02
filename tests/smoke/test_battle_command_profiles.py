from __future__ import annotations

import unittest

from src.perception import BattleCommandProfileCatalog
from tests.smoke._paths import CONFIGS_ROOT


class BattleCommandProfileCatalogTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = BattleCommandProfileCatalog.load(CONFIGS_ROOT / "ui" / "battle-command-profiles.json")

    def test_character_battle_profile_contains_only_main_menu_commands(self) -> None:
        profile = self.catalog.get("character_battle_command_bar")

        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual("character_battle_command_bar", profile.group)
        self.assertEqual(0, len(profile.seed_button_refs))
        self.assertNotIn("pet", profile.labels_by_name)

    def test_pet_battle_profile_contains_only_four_commands(self) -> None:
        profile = self.catalog.get("pet_battle_command_bar")

        self.assertIsNotNone(profile)
        assert profile is not None
        self.assertEqual(("spell", "item", "defend", "protect"), profile.menu_button_names)
        self.assertEqual(0, len(profile.seed_button_refs))


if __name__ == "__main__":
    unittest.main()
