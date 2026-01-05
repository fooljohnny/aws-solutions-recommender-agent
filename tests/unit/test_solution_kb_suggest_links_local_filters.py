from __future__ import annotations

from pathlib import Path

from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.cfn_parser import CloudFormationTemplateParser
from src.services.solution_kb.models import TemplateSource


def test_suggest_links_local_in_direction_and_industry_filter(tmp_path: Path):
    parser = CloudFormationTemplateParser()

    # Template 1 (finance): Lambda Permission references Lambda (incoming to Lambda should count Permission)
    tpl1 = """
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
  MyPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: { Ref: MyFunction }
"""
    ex1 = parser.parse_text(tpl1, source=TemplateSource.LOCAL, name="t1.yaml")
    ex1.meta.industries = ["finance"]

    # Template 2 (retail): S3 -> Lambda reference
    tpl2 = """
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
  MyFunction:
    Type: AWS::Lambda::Function
    Properties:
      Environment:
        Variables:
          B: { Ref: MyBucket }
"""
    ex2 = parser.parse_text(tpl2, source=TemplateSource.LOCAL, name="t2.yaml")
    ex2.meta.industries = ["retail"]

    store = SolutionKBStore(root_dir=str(tmp_path / "kb"))
    store.upsert_many([ex1, ex2])

    # Incoming edges to Lambda in finance should show IAM Role, not S3.
    pairs = store.suggest_connected_resource_types(
        resource_type="AWS::Lambda::Function",
        direction="in",
        relation="both",
        industries=["finance"],
        limit=10,
    )
    assert pairs[0][0] == "AWS::Lambda::Permission"
    assert all(t != "AWS::S3::Bucket" for t, _ in pairs)

