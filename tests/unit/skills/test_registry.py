import pytest

from src.skills.base import SkillContext, SkillResult
from src.skills.registry import SkillRegistry


class EchoSkill:
    name = "echo"
    description = "Echo args back."

    @property
    def parameters(self):
        return {"type": "object", "properties": {"x": {"type": "string"}}, "required": []}

    async def run(self, args, context: SkillContext) -> SkillResult:
        return SkillResult(ok=True, data={"args": dict(args), "session_id": str(context.session_id) if context.session_id else None})


class BoomSkill:
    name = "boom"
    description = "Always raises."

    @property
    def parameters(self):
        return {"type": "object", "properties": {}, "required": []}

    async def run(self, args, context: SkillContext) -> SkillResult:
        raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_registry_register_and_dispatch_success():
    reg = SkillRegistry()
    reg.register(EchoSkill())

    res = await reg.dispatch("echo", {"x": "y"}, SkillContext())
    assert res.ok is True
    assert res.data["args"]["x"] == "y"


def test_registry_register_duplicate_raises():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    with pytest.raises(ValueError, match="already registered"):
        reg.register(EchoSkill())


@pytest.mark.asyncio
async def test_registry_dispatch_unknown_skill():
    reg = SkillRegistry()
    res = await reg.dispatch("missing", {}, SkillContext())
    assert res.ok is False
    assert "Unknown skill" in (res.error or "")


@pytest.mark.asyncio
async def test_registry_dispatch_exception_is_caught():
    reg = SkillRegistry()
    reg.register(BoomSkill())
    res = await reg.dispatch("boom", {}, SkillContext())
    assert res.ok is False
    assert res.error == "boom"


def test_registry_tool_schemas_shape():
    reg = SkillRegistry()
    reg.register(EchoSkill())
    schemas = reg.get_tool_schemas()
    assert schemas == [
        {
            "name": "echo",
            "description": "Echo args back.",
            "parameters": {"type": "object", "properties": {"x": {"type": "string"}}, "required": []},
        }
    ]

