from __future__ import annotations

from uuid import uuid4

from src.models.user_requirement import RequirementType, UserRequirement
from src.services.solution_kb.ranking import HybridRanker, RankWeights
from src.services.solution_kb.models import TemplateExtract, TemplateMetadata, TemplateSource, TemplateKind


def test_ranking_prefers_trusted_source_when_scores_equal():
    # Two templates with same text, different source. QuickStart should rank higher by prior.
    t1 = TemplateExtract(
        meta=TemplateMetadata(
            kind=TemplateKind.CLOUDFORMATION,
            source=TemplateSource.AWS_QUICKSTART,
            name="web stack",
            description="high availability",
            tags=["web"],
            industries=["finance"],
            business_types=["payments"],
        ),
        resource_types=["AWS::Lambda::Function"],
    )
    t2 = TemplateExtract(
        meta=TemplateMetadata(
            kind=TemplateKind.CLOUDFORMATION,
            source=TemplateSource.COMMUNITY,
            name="web stack",
            description="high availability",
            tags=["web"],
            industries=["finance"],
            business_types=["payments"],
        ),
        resource_types=["AWS::Lambda::Function"],
    )
    # Make semantic score irrelevant for determinism in tests
    ranker = HybridRanker(weights=RankWeights(semantic_sim=0.0))

    reqs = [
        UserRequirement(
            session_id=uuid4(),
            requirement_type=RequirementType.CONSTRAINT,
            requirement_value="金融 支付 高可用",
            confidence=0.9,
        )
    ]
    ranked = ranker.rank(requirements=reqs, candidates=[t2, t1], keywords=["金融", "支付", "高可用"], limit=2)
    assert ranked[0][0].meta.source == TemplateSource.AWS_QUICKSTART


def test_synonym_normalization_matches_finance_chinese_token():
    t = TemplateExtract(
        meta=TemplateMetadata(
            kind=TemplateKind.CLOUDFORMATION,
            source=TemplateSource.AWS_SOLUTIONS,
            name="payments ref",
            industries=["finance"],
            business_types=["payments"],
            tags=[],
        ),
        resource_types=[],
    )
    ranker = HybridRanker(weights=RankWeights(semantic_sim=0.0))
    reqs = [
        UserRequirement(
            session_id=uuid4(),
            requirement_type=RequirementType.CONSTRAINT,
            requirement_value="金融",
            confidence=0.9,
        )
    ]
    ranked = ranker.rank(requirements=reqs, candidates=[t], keywords=["金融"], limit=1)
    assert ranked[0][1] > 0.0

