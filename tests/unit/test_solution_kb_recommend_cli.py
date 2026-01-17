from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli.kb import app as kb_app
from src.services.solution_kb.cfn_parser import CloudFormationTemplateParser
from src.services.solution_kb.models import TemplateSource
from src.services.solution_kb.store import SolutionKBStore


def _store_with_template(tmp_path: Path):
    parser = CloudFormationTemplateParser()
    tpl = "\n".join(
        [
            "AWSTemplateFormatVersion: '2010-09-09'",
            "Description: payments web stack",
            "Resources:",
            "  MyBucket:",
            "    Type: AWS::S3::Bucket",
            "",
        ]
    )
    ex = parser.parse_text(tpl, source=TemplateSource.LOCAL, name="payments.yaml")
    ex.meta.name = "payments web"
    ex.meta.tags = ["payments", "web"]
    ex.meta.template_body = tpl + "\n"

    store = SolutionKBStore(root_dir=str(tmp_path / "kb"))
    store.upsert_many([ex])
    return store, ex


def test_cli_recommend_outputs_template(tmp_path: Path):
    store, ex = _store_with_template(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        kb_app,
        [
            "recommend",
            "payments web",
            "--no-clarify",
            "--kb-dir",
            str(store.root_dir),
        ],
    )
    assert result.exit_code == 0
    assert str(ex.meta.template_id) in result.output


def test_cli_recommend_export(tmp_path: Path):
    store, ex = _store_with_template(tmp_path)
    out_dir = tmp_path / "export"
    runner = CliRunner()
    result = runner.invoke(
        kb_app,
        [
            "recommend",
            "payments web",
            "--no-clarify",
            "--kb-dir",
            str(store.root_dir),
            "--export",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0
    exported = out_dir / f"{ex.meta.template_id}.yaml"
    assert exported.exists()
    assert exported.read_text(encoding="utf-8").startswith("AWSTemplateFormatVersion")
