from uuid import uuid4

from src.models.user_requirement import RequirementType, UserRequirement
from src.services.solution_kb.models import (
    ParameterSpec,
    ResourceSpec,
    TemplateExtract,
    TemplateKind,
    TemplateMetadata,
    TemplateSource,
)
from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.retriever import SolutionTemplateRetriever
from src.services.recommendation.solution_kb_recommendation import SolutionKBRecommendationService


def _req(session_id, t: RequirementType, v: str, conf: float = 0.9):
    return UserRequirement(
        session_id=session_id,
        requirement_type=t,
        requirement_value=v,
        confidence=conf,
    )


def _template(*, name: str, usage: int, resources: list[ResourceSpec], params: list[ParameterSpec] | None = None):
    meta = TemplateMetadata(
        kind=TemplateKind.CLOUDFORMATION,
        source=TemplateSource.LOCAL,
        name=name,
        description=f"{name} desc",
        usage_count=usage,
    )
    return TemplateExtract(
        meta=meta,
        parameters=params or [],
        resources=resources,
        outputs=[],
        resource_types=[r.type for r in resources],
    )


def test_fallback_top_by_usage_when_no_match_and_no_more_clarification(tmp_path):
    # Create a KB store with templates but no keyword matches for the query.
    store = SolutionKBStore(root_dir=str(tmp_path))
    t1 = _template(
        name="Popular A",
        usage=100,
        resources=[ResourceSpec(logical_id="Web", type="AWS::EC2::Instance")],
    )
    t2 = _template(
        name="Popular B",
        usage=80,
        resources=[ResourceSpec(logical_id="Db", type="AWS::RDS::DBInstance")],
    )
    t3 = _template(
        name="Popular C",
        usage=60,
        resources=[ResourceSpec(logical_id="Asg", type="AWS::AutoScaling::AutoScalingGroup")],
    )
    store.upsert_many([t3, t2, t1])

    retriever = SolutionTemplateRetriever(store=store)
    svc = SolutionKBRecommendationService(retriever=retriever)

    session_id = uuid4()
    # Sparse requirements: triggers clarifier, but we've already used 2 rounds.
    requirements = [_req(session_id, RequirementType.APPLICATION_TYPE, "一个系统", 0.9)]

    result = svc.recommend(requirements, clarification_rounds_used=2, limit=3)

    assert result.needs_clarification is False
    assert result.fallback_top_by_usage is True
    assert [r.template.meta.name for r in result.recommended] == ["Popular A", "Popular B", "Popular C"]


def test_clarification_requested_when_under_cap(tmp_path):
    store = SolutionKBStore(root_dir=str(tmp_path))
    store.upsert_many(
        [
            _template(
                name="Whatever",
                usage=1,
                resources=[ResourceSpec(logical_id="Web", type="AWS::EC2::Instance")],
            )
        ]
    )
    retriever = SolutionTemplateRetriever(store=store)
    svc = SolutionKBRecommendationService(retriever=retriever)

    session_id = uuid4()
    # Missing scale/constraint/preference should trigger clarifier
    requirements = [_req(session_id, RequirementType.APPLICATION_TYPE, "web 应用", 0.9)]

    result = svc.recommend(requirements, clarification_rounds_used=0, limit=3)
    assert result.needs_clarification is True
    assert result.clarification_questions

