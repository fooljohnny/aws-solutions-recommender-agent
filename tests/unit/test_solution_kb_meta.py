from __future__ import annotations

from pathlib import Path

from src.services.solution_kb.meta import parse_meta_file


def test_parse_single_template_meta_yaml(tmp_path: Path):
    p = tmp_path / "kb.meta.yaml"
    p.write_text(
        """
name: "电商Web高可用"
description: "面向电商的高可用Web应用参考架构"
tags: ["高可用", "电商", "三层架构"]
industries: ["零售"]
business_types: ["电商"]
""".strip(),
        encoding="utf-8",
    )

    spec = parse_meta_file(p)
    assert spec.default is not None
    assert spec.default.name == "电商Web高可用"
    assert "零售" in spec.default.industries
    assert "电商" in spec.default.business_types


def test_parse_multi_template_meta_yaml(tmp_path: Path):
    p = tmp_path / "kb.meta.yaml"
    p.write_text(
        """
default:
  tags: ["官方模板"]
templates:
  - path: template-a.yaml
    name: "A"
    tags: ["a1"]
  - path: template-b.yaml
    name: "B"
    industries: ["金融"]
""".strip(),
        encoding="utf-8",
    )

    spec = parse_meta_file(p)
    assert spec.default is not None
    assert len(spec.templates) == 2
