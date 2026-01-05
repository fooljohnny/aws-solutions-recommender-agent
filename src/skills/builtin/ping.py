"""A minimal built-in skill for smoke-testing the framework."""

from __future__ import annotations

from typing import Any, Mapping

from ..base import SkillContext, SkillResult


class PingSkill:
    name = "ping"
    description = "Health-check skill that echoes back the provided message."

    @property
    def parameters(self) -> Mapping[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo back",
                }
            },
            "required": [],
        }

    async def run(self, args: Mapping[str, Any], context: SkillContext) -> SkillResult:
        message = args.get("message", "pong")
        return SkillResult(ok=True, data={"message": message, "session_id": str(context.session_id) if context.session_id else None})

