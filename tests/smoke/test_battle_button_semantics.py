from __future__ import annotations

import unittest
from datetime import datetime, timezone

from src.domain import BattleObservation, MatchResult
from src.perception import BattleButtonSemanticCatalog
from tests.smoke._paths import CONFIGS_ROOT


def build_observation(*template_ids: str) -> BattleObservation:
    return BattleObservation(
        battle_ui_visible=True,
        action_prompt_visible="battle_action_prompt" in template_ids,
        skill_panel_visible="battle_skill_bar" in template_ids,
        target_select_visible="battle_target_panel" in template_ids,
        settlement_visible=False,
        window_alive=True,
        window_focused=True,
        frame_timestamp=datetime.now(timezone.utc),
        frame_hash="frame-hash",
        confidence_summary=0.95,
        matches=tuple(
            MatchResult(template_id=template_id, confidence=0.99, region_name="test")
            for template_id in template_ids
        ),
    )


class BattleButtonSemanticCatalogTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = BattleButtonSemanticCatalog.load(CONFIGS_ROOT / "ui" / "battle-button-semantics.json")

    def test_defend_confirms_when_action_prompt_disappears(self) -> None:
        before = build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar")
        after = build_observation("battle_ui", "battle_skill_bar")

        result = self.catalog.verify("battle_command_bar.defend", before, after)

        self.assertTrue(result.confirmed)
        self.assertEqual("ready", result.verification_status)

    def test_defend_fails_when_action_prompt_still_present(self) -> None:
        before = build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar")
        after = build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar")

        result = self.catalog.verify("battle_command_bar.defend", before, after)

        self.assertFalse(result.confirmed)
        self.assertIn("still present", result.reason)

    def test_item_reports_blocked_when_required_template_is_missing(self) -> None:
        before = build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar")
        after = build_observation("battle_ui", "battle_skill_bar")

        result = self.catalog.verify("battle_command_bar.item", before, after)

        self.assertFalse(result.confirmed)
        self.assertEqual("blocked_by_missing_template", result.verification_status)

    def test_unknown_button_ref_reports_missing_rule(self) -> None:
        before = build_observation("battle_ui", "battle_action_prompt")
        after = build_observation("battle_ui")

        result = self.catalog.verify("battle_command_bar.unknown", before, after)

        self.assertFalse(result.confirmed)
        self.assertEqual("missing_rule", result.verification_status)

    def test_character_battle_defend_uses_independent_semantic_rule(self) -> None:
        before = build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar")
        after = build_observation("battle_ui", "battle_skill_bar")

        result = self.catalog.verify("character_battle_command_bar.defend", before, after)

        self.assertTrue(result.confirmed)
        self.assertEqual("ready", result.verification_status)

    def test_pet_battle_defend_uses_independent_semantic_rule(self) -> None:
        before = build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar")
        after = build_observation("battle_ui", "battle_skill_bar")

        result = self.catalog.verify("pet_battle_command_bar.defend", before, after)

        self.assertTrue(result.confirmed)
        self.assertEqual("ready", result.verification_status)

    def test_character_battle_escape_uses_ready_semantic_rule(self) -> None:
        before = build_observation("battle_ui", "battle_action_prompt", "battle_skill_bar")
        after = build_observation("battle_ui", "battle_skill_bar")

        result = self.catalog.verify("character_battle_command_bar.escape", before, after)

        self.assertTrue(result.confirmed)
        self.assertEqual("ready", result.verification_status)


if __name__ == "__main__":
    unittest.main()
