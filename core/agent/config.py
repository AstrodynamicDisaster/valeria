"""
Configuration constants for the Valeria agent.

Centralises model IDs, batching parameters, and feature toggles so they can be
modified without touching the core logic.
"""

from dataclasses import dataclass
from typing import Final

# OpenAI model defaults
DEFAULT_CHAT_MODEL: Final[str] = "gpt-4.1-nano-2025-04-14"

# Batch processing configuration
BATCH_COMMIT_SIZE: Final[int] = 1


@dataclass(frozen=True)
class FeatureFlags:
    """
    Feature toggles that can be wired into the agent. Keeping them in a dataclass
    allows tests to override values easily.
    """

    enable_concept_mapping: bool = False


FEATURE_FLAGS = FeatureFlags()
