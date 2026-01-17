from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli.kb import app as kb_app
from src.services.solution_kb.cfn_parser import CloudFormationTemplateParser
from src.services.solution_kb.models import TemplateSource
from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.suggester import suggest_next_resource_types


def _build_store(tmp_path: Path) -> SolutionKBStore:
    parser = CloudFormationTemplateParser()

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
"""
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
    ex1 = parser.parse_text(tpl1, source=TemplateSource.LOCAL, name="t1.yaml")
    ex2 = parser.parse_text(tpl2, source=TemplateSource.LOCAL, name="t2.yaml")

    store = SolutionKBStore(root_dir=str(tmp_path / "kb"))
    store.upsert_many([ex1, ex2])
    return store


def test_suggest_next_resource_types_aggregates_counts(tmp_path: Path):
    store = _build_store(tmp_path)
    pairs = suggest_next_resource_types(
        store,
        ["AWS::Lambda::Function", "AWS::S3::Bucket"],
        relation="both",
        direction="both",
        exclude_present=False,
        limit=10,
    )
    as_dict = dict(pairs)
    assert as_dict["AWS::IAM::Role"] == 2
    assert as_dict["AWS::S3::Bucket"] == 1
    assert as_dict["AWS::Lambda::Function"] == 1


def test_suggest_next_resource_types_excludes_existing(tmp_path: Path):
    store = _build_store(tmp_path)
    pairs = suggest_next_resource_types(
        store,
        ["AWS::Lambda::Function", "AWS::S3::Bucket"],
        relation="both",
        direction="both",
        exclude_present=True,
        limit=10,
    )
    as_dict = dict(pairs)
    assert as_dict["AWS::IAM::Role"] == 2
    assert "AWS::S3::Bucket" not in as_dict
    assert "AWS::Lambda::Function" not in as_dict


def test_cli_suggest_next(tmp_path: Path):
    store = _build_store(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        kb_app,
        [
            "suggest-next",
            "--resource-types",
            "AWS::Lambda::Function,AWS::S3::Bucket",
            "--relation",
            "both",
            "--direction",
            "both",
            "--include-existing",
            "--kb-dir",
            str(store.root_dir),
        ],
    )
    assert result.exit_code == 0
    assert "AWS::IAM::Role" in result.output
