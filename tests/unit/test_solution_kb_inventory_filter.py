from uuid import uuid4

from src.models.user_requirement import RequirementType, UserRequirement
from src.services.product_catalog.catalog import ProductCatalog
from src.services.product_catalog.models import ProductOffering
from src.services.recommendation.solution_kb_recommendation import SolutionKBRecommendationService
from src.services.solution_kb.models import ResourceSpec, TemplateExtract, TemplateKind, TemplateMetadata, TemplateSource
from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.retriever import SolutionTemplateRetriever


def _req(session_id, t: RequirementType, v: str, conf: float = 0.9):
    return UserRequirement(
        session_id=session_id,
        requirement_type=t,
        requirement_value=v,
        confidence=conf,
    )


def _template(name: str, resources: list[ResourceSpec]):
    meta = TemplateMetadata(kind=TemplateKind.CLOUDFORMATION, source=TemplateSource.LOCAL, name=name, usage_count=1)
    return TemplateExtract(
        meta=meta,
        parameters=[],
        resources=resources,
        outputs=[],
        resource_types=[r.type for r in resources],
    )


def test_inventory_and_az_constraints_filter_out_unfulfillable_templates(tmp_path):
    # Catalog: t3.large has 0 inventory in us-east-1c
    catalog = ProductCatalog(
        offerings=[
            ProductOffering(
                sku="ec2.t3.large.us-east-1",
                service_name="EC2",
                region="us-east-1",
                availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                spec={"instance_type": "t3.large"},
                defaults={},
                inventory_by_az={"us-east-1a": 5, "us-east-1b": 5, "us-east-1c": 0},
                tags=["compute"],
            ),
            ProductOffering(
                sku="ec2.t3.medium.us-east-1",
                service_name="EC2",
                region="us-east-1",
                availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
                spec={"instance_type": "t3.medium"},
                defaults={},
                inventory_by_az={"us-east-1a": 50, "us-east-1b": 50, "us-east-1c": 50},
                tags=["compute"],
            ),
        ]
    )

    # Two templates: one EC2 (defaults to t3.medium) is ok; one ASG (needs qty=2) ok.
    # We'll force t3.large default by putting a parameter named InstanceType.
    from src.services.solution_kb.models import ParameterSpec

    t_ok = _template(name="OK", resources=[ResourceSpec(logical_id="Web", type="AWS::EC2::Instance")])
    t_bad = TemplateExtract(
        meta=TemplateMetadata(kind=TemplateKind.CLOUDFORMATION, source=TemplateSource.LOCAL, name="BAD", usage_count=10),
        parameters=[ParameterSpec(name="InstanceType", default="t3.large")],
        resources=[ResourceSpec(logical_id="Web", type="AWS::EC2::Instance")],
        outputs=[],
        resource_types=["AWS::EC2::Instance"],
    )

    store = SolutionKBStore(root_dir=str(tmp_path))
    store.upsert_many([t_ok, t_bad])

    retriever = SolutionTemplateRetriever(store=store)
    svc = SolutionKBRecommendationService(retriever=retriever, catalog=catalog)

    session_id = uuid4()
    # Force AZ us-east-1c in preferences => t3.large offering cannot be used
    reqs = [
        _req(session_id, RequirementType.APPLICATION_TYPE, "web", 0.9),
        _req(session_id, RequirementType.PREFERENCE, "region us-east-1, az us-east-1c", 0.9),
        _req(session_id, RequirementType.SCALE, "小规模", 0.9),
        _req(session_id, RequirementType.CONSTRAINT, "成本优化", 0.9),
    ]

    result = svc.recommend(reqs, clarification_rounds_used=2, limit=3)
    names = [r.template.meta.name for r in result.recommended]
    assert "OK" in names
    assert "BAD" not in names

