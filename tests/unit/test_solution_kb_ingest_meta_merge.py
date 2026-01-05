from __future__ import annotations

from pathlib import Path

from src.services.solution_kb.ingest import SolutionKBIngestor
from src.services.solution_kb.store import SolutionKBStore
from src.services.solution_kb.models import TemplateSource


def test_ingest_merges_kb_meta_yaml_into_template_metadata(tmp_path: Path):
    # Layout:
    # tmp/stack/template.yaml
    # tmp/stack/kb.meta.yaml
    stack = tmp_path / "stack"
    stack.mkdir()

    tpl = stack / "template.yaml"
    tpl.write_text(
        """
AWSTemplateFormatVersion: '2010-09-09'
Description: From template file
Resources:
  MyBucket:
    Type: AWS::S3::Bucket
""".strip(),
        encoding="utf-8",
    )

    meta = stack / "kb.meta.yaml"
    meta.write_text(
        """
name: "运营标注名称"
description: "运营标注描述"
source: aws_sar
tags: ["serverless", "prod"]
industries: ["finance"]
business_types: ["payments"]
""".strip(),
        encoding="utf-8",
    )

    store = SolutionKBStore(root_dir=str(tmp_path / "kb"))
    ingestor = SolutionKBIngestor(store=store)
    stats = ingestor.ingest_path(str(tpl), source=TemplateSource.LOCAL, repository="repo-x")
    assert stats.parsed == 1

    items = store.list_all()
    assert len(items) == 1
    ex = items[0]
    assert ex.meta.name == "运营标注名称"
    assert ex.meta.description == "运营标注描述"
    assert ex.meta.source == TemplateSource.AWS_SAR
    assert set(ex.meta.tags) >= {"serverless", "prod"}
    assert ex.meta.industries == ["finance"]
    assert ex.meta.business_types == ["payments"]

