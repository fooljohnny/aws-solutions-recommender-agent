from __future__ import annotations

from uuid import uuid4

from src.models.user_requirement import RequirementType, UserRequirement
from src.services.solution_kb.clarifier import KBClarificationService
from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.retriever import SolutionTemplateRetriever
from src.services.solution_kb.cfn_parser import CloudFormationTemplateParser
from src.services.solution_kb.models import TemplateSource


def test_kb_clarifier_asks_missing_scale_and_discriminative_questions(tmp_path):
    # Create a KB with two candidate templates that differ on DB choice.
    parser = CloudFormationTemplateParser()
    t_rds = parser.parse_text(
        """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  Db:
    Type: AWS::RDS::DBInstance
  Fn:
    Type: AWS::Lambda::Function
""",
        source=TemplateSource.LOCAL,
        name="rds.yaml",
    )
    t_rds.meta.tags = ["web"]

    t_ddb = parser.parse_text(
        """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  Table:
    Type: AWS::DynamoDB::Table
  Fn:
    Type: AWS::Lambda::Function
""",
        source=TemplateSource.LOCAL,
        name="ddb.yaml",
    )
    t_ddb.meta.tags = ["web"]

    store = SolutionKBStore(root_dir=str(tmp_path / "kb"))
    store.upsert_many([t_rds, t_ddb])

    retriever = SolutionTemplateRetriever(store=store)
    clarifier = KBClarificationService(retriever=retriever)

    # User provided application type but missing scale/constraints.
    reqs = [
        UserRequirement(
            session_id=uuid4(),
            requirement_type=RequirementType.APPLICATION_TYPE,
            requirement_value="web应用",
            confidence=0.9,
        )
    ]
    plan = clarifier.plan(reqs, limit=4)
    assert plan.needs_clarification is True
    # Expect a scale question
    assert any("规模" in q or "QPS" in q for q in plan.questions)
    # Expect a DB disambiguation question
    assert any("RDS" in q or "DynamoDB" in q or "关系型" in q for q in plan.questions)

