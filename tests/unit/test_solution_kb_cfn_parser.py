from __future__ import annotations

from src.services.solution_kb.cfn_parser import CloudFormationTemplateParser
from src.services.solution_kb.models import TemplateSource


def test_parse_cloudformation_yaml_extracts_resources_parameters_and_references():
    tpl = """
AWSTemplateFormatVersion: '2010-09-09'
Description: Simple web stack
Parameters:
  Env:
    Type: String
    Default: dev
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
  MyRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
  MyFunction:
    Type: AWS::Lambda::Function
    DependsOn: MyRole
    Properties:
      Role:
        Fn::GetAtt: [MyRole, Arn]
      Environment:
        Variables:
          BUCKET: { Ref: MyBucket }
Outputs:
  BucketName:
    Value: { Ref: MyBucket }
    Export:
      Name:
        Fn::Sub: "${Env}-bucket"
"""
    parser = CloudFormationTemplateParser()
    ex = parser.parse_text(tpl, source=TemplateSource.LOCAL, name="sample.yaml")

    assert ex.meta.description == "Simple web stack"
    assert [p.name for p in ex.parameters] == ["Env"]
    assert {r.logical_id for r in ex.resources} == {"MyBucket", "MyRole", "MyFunction"}
    assert "AWS::Lambda::Function" in ex.resource_types

    fn = next(r for r in ex.resources if r.logical_id == "MyFunction")
    assert "MyRole" in fn.depends_on
    assert set(fn.references) >= {"MyRole", "MyBucket"}

    out = next(o for o in ex.outputs if o.name == "BucketName")
    assert "MyBucket" in out.references

