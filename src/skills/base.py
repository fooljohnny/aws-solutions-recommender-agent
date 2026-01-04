"""Core types for the skills framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Protocol
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass(slots=True)
class SkillContext:
    """Execution context provided to skills."""

    session_id: Optional[UUID] = None
    llm_provider: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillResult(BaseModel):
    """Structured skill result returned to the caller (and optionally to an LLM)."""

    ok: bool = Field(description="Whether the skill execution succeeded")
    data: Any | None = Field(default=None, description="Successful result payload (JSON-serializable)")
    error: str | None = Field(default=None, description="Error message if ok is False")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Optional extra metadata")


class Skill(Protocol):
    """A runnable capability with a tool-like schema."""

    name: str
    description: str

    @property
    def parameters(self) -> Mapping[str, Any]:
        """JSON schema object describing the skill input."""

    async def run(self, args: Mapping[str, Any], context: SkillContext) -> SkillResult:
        """Execute the skill."""

