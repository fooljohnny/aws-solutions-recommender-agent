from __future__ import annotations

from pathlib import Path

from src.services.solution_kb.meta import parse_meta_file, pick_annotation_for_template
from src.services.solution_kb.models import TemplateSource


def test_meta_single_template_mode(tmp_path: Path):
    meta_path = tmp_path / "kb.meta.yaml"
    meta_path.write_text(
        """
name: "电商高可用 Web"
description: "ALB + EC2 + RDS，多可用区"
source: aws_quickstart
tags: ["high-availability", "web"]
industries: ["retail"]
business_types: ["ecommerce"]
""".strip(),
        encoding="utf-8",
    )

    spec = parse_meta_file(meta_path)
    assert spec.default is not None
    assert spec.default.name == "电商高可用 Web"
    assert spec.default.source == TemplateSource.AWS_QUICKSTART


def test_meta_multi_template_mode_path_match_and_default_merge(tmp_path: Path):
    meta_path = tmp_path / "kb.meta.yaml"
    meta_path.write_text(
        """
default:
  source: aws_solutions
  tags: ["prod-ready"]
templates:
  - path: "a/template.yaml"
    name: "方案A"
    tags: ["web"]
  - path: "b/template.yaml"
    name: "方案B"
    tags: ["data"]
""".strip(),
        encoding="utf-8",
    )

    (tmp_path / "a").mkdir()
    tpl_a = tmp_path / "a" / "template.yaml"
    tpl_a.write_text("Resources: {}", encoding="utf-8")

    spec = parse_meta_file(meta_path)
    ann = pick_annotation_for_template(spec, tpl_a, base_dir=meta_path.parent)
    assert ann is not None
    assert ann.name == "方案A"
    assert ann.source == TemplateSource.AWS_SOLUTIONS
    assert set(ann.tags) == {"prod-ready", "web"}
