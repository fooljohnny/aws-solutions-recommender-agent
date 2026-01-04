from __future__ import annotations

from pathlib import Path

from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.cfn_parser import CloudFormationTemplateParser
from src.services.solution_kb.models import TemplateSource


def test_suggest_connected_resource_types_local_store_counts_edges(tmp_path: Path):
    tpl = """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  MyRole:
    Type: AWS::IAM::Role
  MyFunction:
    Type: AWS::Lambda::Function
    DependsOn: MyRole
    Properties:
      Role:
        Fn::GetAtt: [MyRole, Arn]
Outputs: {}
"""
    parser = CloudFormationTemplateParser()
    ex = parser.parse_text(tpl, source=TemplateSource.LOCAL, name="t.yaml")

    store = SolutionKBStore(root_dir=str(tmp_path / "kb"))
    store.upsert_many([ex])

    pairs = store.suggest_connected_resource_types(
        resource_type="AWS::Lambda::Function",
        relation="both",
        limit=10,
    )
    # Lambda->IAM Role should be counted twice (DependsOn + References)
    assert pairs[0][0] == "AWS::IAM::Role"
    assert pairs[0][1] == 2

