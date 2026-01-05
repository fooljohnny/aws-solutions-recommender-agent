"""Skills framework: registry + runnable capabilities for an agent.

A "skill" is a small, well-scoped unit of work that:
- exposes a tool-like JSON schema (name/description/parameters)
- can be executed with validated/structured arguments
- returns structured results (ok/data/error) for downstream reasoning
"""

from .base import Skill, SkillContext, SkillResult
from .registry import SkillRegistry

__all__ = [
    "Skill",
    "SkillContext",
    "SkillResult",
    "SkillRegistry",
]

