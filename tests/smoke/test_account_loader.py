from __future__ import annotations

import unittest

from src.app import AccountBindingLoader
from tests.smoke._paths import CONFIGS_ROOT


class AccountBindingLoaderTestCase(unittest.TestCase):
    def test_loads_instance_binding_with_character_and_window_info(self) -> None:
        binding = AccountBindingLoader().load(CONFIGS_ROOT / "accounts" / "instance-1.json")

        self.assertEqual("instance-1", binding.instance_id)
        self.assertTrue(binding.enabled)
        self.assertEqual("../characters/mage-default.json", binding.character_config_ref)
        self.assertEqual(264972, binding.window.handle)
        self.assertEqual("DHXYFreeJYMainFrame", binding.window.class_name)


if __name__ == "__main__":
    unittest.main()
