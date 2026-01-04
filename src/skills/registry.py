"""Skill registry and dispatcher."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from .base import Skill, SkillContext, SkillResult


class SkillRegistry:
    """In-memory skill registry with safe dispatch."""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill by its unique name."""
        name = getattr(skill, "name", None)
        if not name or not isinstance(name, str):
            raise ValueError("Skill must have a non-empty string 'name'")
        if name in self._skills:
            raise ValueError(f"Skill already registered: {name}")
        self._skills[name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list(self) -> Iterable[Skill]:
        return self._skills.values()

    def get_tool_schemas(self) -> list[Dict[str, Any]]:
        """Return OpenAI-style tool schema objects (name/description/parameters)."""
        schemas: list[Dict[str, Any]] = []
        for skill in self._skills.values():
            schemas.append(
                {
                    "name": skill.name,
                    "description": skill.description,
                    "parameters": dict(skill.parameters),
                }
            )
        return schemas

    async def dispatch(self, name: str, args: Mapping[str, Any], context: SkillContext) -> SkillResult:
        """Execute a skill safely (not found / exceptions become structured errors)."""
        skill = self.get(name)
        if not skill:
            return SkillResult(ok=False, error=f"Unknown skill: {name}")

        try:
            result = await skill.run(args=args, context=context)
        except Exception as e:  # noqa: BLE001 - we intentionally catch to return structured error
            return SkillResult(ok=False, error=str(e))

        # Ensure result shape
        if not isinstance(result, SkillResult):
            return SkillResult(ok=False, error="Skill returned invalid result type")
        return result

