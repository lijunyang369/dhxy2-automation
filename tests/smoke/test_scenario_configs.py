from __future__ import annotations

import json
import unittest

from tests.smoke._paths import CONFIGS_ROOT


class ScenarioConfigTestCase(unittest.TestCase):
    def test_character_battle_defend_scenario_points_to_character_button_ref(self) -> None:
        payload = json.loads((CONFIGS_ROOT / "scenarios" / "character-battle-defend.json").read_text(encoding="utf-8-sig"))

        self.assertEqual("CLICK_UI_BUTTON", payload["primary_rule"]["action_type"])
        self.assertEqual("battle_command_bar.defend", payload["primary_rule"]["parameters"]["button_ref"])
        self.assertEqual("character_battle_command_bar", payload["primary_rule"]["target"])

    def test_pet_battle_defend_scenario_points_to_pet_button_ref(self) -> None:
        payload = json.loads((CONFIGS_ROOT / "scenarios" / "pet-battle-defend.json").read_text(encoding="utf-8-sig"))

        self.assertEqual("CLICK_UI_BUTTON", payload["primary_rule"]["action_type"])
        self.assertEqual("pet_battle_command_bar.defend", payload["primary_rule"]["parameters"]["button_ref"])
        self.assertEqual("pet_battle_command_bar", payload["primary_rule"]["target"])


if __name__ == "__main__":
    unittest.main()
