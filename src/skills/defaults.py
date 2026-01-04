"""Factory for the default skill registry used by the app."""

from __future__ import annotations

from .builtin import PingSkill
from .registry import SkillRegistry


def create_default_registry() -> SkillRegistry:
    registry = SkillRegistry()
    registry.register(PingSkill())
    return registry

