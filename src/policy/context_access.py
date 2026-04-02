from __future__ import annotations

from src.domain import AutomationContext, CharacterProfile
from src.policy.exceptions import PolicyDecisionError


def require_character_profile(context: AutomationContext) -> CharacterProfile:
    profile = context.character_profile
    if profile is None:
        raise PolicyDecisionError(f"instance {context.instance_id} has no bound character profile")
    return profile
