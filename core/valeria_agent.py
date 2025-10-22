"""
Legacy import shim for the Valeria agent.

The actual implementation lives under `core.agent.agent`. This file remains to
avoid breaking existing imports that expect the historical module path.
"""

from core.agent.agent import ValeriaAgent

__all__ = ["ValeriaAgent"]
