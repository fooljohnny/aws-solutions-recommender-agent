from uuid import uuid4

from src.models.context import Context
from src.models.user_requirement import RequirementType, UserRequirement
from src.services.conversation.solution_conversation import SolutionConversationService
from src.services.product_catalog.catalog import ProductCatalog
from src.services.product_catalog.models import ProductOffering
from src.services.solution_kb.models import ResourceSpec, TemplateExtract, TemplateKind, TemplateMetadata, TemplateSource
from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.retriever import SolutionTemplateRetriever


def _req(session_id, t: RequirementType, v: str, conf: float = 0.9):
    return UserRequirement(session_id=session_id, requirement_type=t, requirement_value=v, confidence=conf)


def _template(name: str, usage: int = 1):
    meta = TemplateMetadata(kind=TemplateKind.CLOUDFORMATION, source=TemplateSource.LOCAL, name=name, usage_count=usage)
    return TemplateExtract(
        meta=meta,
        parameters=[],
        resources=[ResourceSpec(logical_id="Web", type="AWS::EC2::Instance")],
        outputs=[],
        resource_types=["AWS::EC2::Instance"],
    )


def test_recommend_then_select_then_modify(tmp_path):
    # Setup KB with two templates
    store = SolutionKBStore(root_dir=str(tmp_path))
    t1 = _template("S1", usage=10)
    t2 = _template("S2", usage=5)
    store.upsert_many([t1, t2])
    retriever = SolutionTemplateRetriever(store=store)

    # Catalog with enough inventory
    catalog = ProductCatalog(
        offerings=[
            ProductOffering(
                sku="ec2.t3.medium.us-east-1",
                service_name="EC2",
                region="us-east-1",
                availability_zones=["us-east-1a", "us-east-1b"],
                spec={"instance_type": "t3.medium"},
                defaults={"os": "linux"},
                inventory_by_az={"us-east-1a": 10, "us-east-1b": 10},
                tags=["compute"],
            )
        ]
    )

    svc = SolutionConversationService(retriever=retriever, catalog=catalog)

    session_id = uuid4()
    requirements = [
        _req(session_id, RequirementType.APPLICATION_TYPE, "web", 0.9),
        _req(session_id, RequirementType.SCALE, "小规模", 0.9),
        _req(session_id, RequirementType.CONSTRAINT, "成本优化", 0.9),
        _req(session_id, RequirementType.PREFERENCE, "us-east-1 us-east-1a", 0.9),
    ]

    # Step 1: recommend
    out1 = svc.handle(user_message="给我方案", requirements=requirements, context=None)
    assert "方案候选" in out1.content_markdown
    assert "选择 1/2/3" in out1.content_markdown
    assert "last_recommended_template_ids" in out1.updated_context_fields

    # Build context as if persisted
    ctx = Context(
        session_id=session_id,
        extracted_requirements=requirements,
        last_recommended_template_ids=out1.updated_context_fields["last_recommended_template_ids"],
        clarification_rounds_used=0,
        selected_region="us-east-1",
        selected_azs=["us-east-1a"],
    )

    # Step 2: select
    out2 = svc.handle(user_message="选择 1", requirements=requirements, context=ctx, unit_price_per_hour_by_sku={"ec2.t3.medium.us-east-1": 0.0416})
    assert "配置清单" in out2.content_markdown
    assert "报价估计" in out2.content_markdown
    assert "selected_template_id" in out2.updated_context_fields

    # Update context to selected
    ctx.selected_template_id = out2.updated_context_fields["selected_template_id"]
    ctx.selected_fulfillment = out2.updated_context_fields["selected_fulfillment"]

    # Step 3: modify
    out3 = svc.handle(
        user_message="EC2 两台，multi_az=false",
        requirements=requirements,
        context=ctx,
        unit_price_per_hour_by_sku={"ec2.t3.medium.us-east-1": 0.0416},
    )
    assert "已按您的调整更新" in out3.content_markdown

