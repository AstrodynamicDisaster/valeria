"""
Valeria Agent package.

Provides a modular breakdown of the payroll processing agent so that each concern
is implemented in a dedicated module. The public API exposes `ValeriaAgent`
for backwards compatibility with the legacy import paths.
"""

from .agent import ValeriaAgent

__all__ = ["ValeriaAgent"]
