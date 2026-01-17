from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from src.cli.kb import app as kb_app
from src.services.solution_kb.exporter import load_template_body
from src.services.solution_kb.ingest import SolutionKBIngestor
from src.services.solution_kb.models import TemplateExtract, TemplateKind, TemplateMetadata, TemplateSource
from src.services.solution_kb.store import SolutionKBStore


def test_load_template_body_prefers_inline():
    meta = TemplateMetadata(
        kind=TemplateKind.CLOUDFORMATION,
        source=TemplateSource.LOCAL,
        name="inline",
        template_body="AWSTemplateFormatVersion: '2010-09-09'\nResources: {}\n",
    )
    tpl = TemplateExtract(meta=meta, parameters=[], resources=[], outputs=[], resource_types=[])
    assert load_template_body(tpl).startswith("AWSTemplateFormatVersion")


def test_load_template_body_reads_path(tmp_path: Path):
    path = tmp_path / "t.yaml"
    path.write_text("AWSTemplateFormatVersion: '2010-09-09'\nResources: {}\n", encoding="utf-8")
    meta = TemplateMetadata(
        kind=TemplateKind.CLOUDFORMATION,
        source=TemplateSource.LOCAL,
        name="path",
        path=str(path),
    )
    tpl = TemplateExtract(meta=meta, parameters=[], resources=[], outputs=[], resource_types=[])
    assert load_template_body(tpl).startswith("AWSTemplateFormatVersion")


def test_cli_export_template_body(tmp_path: Path):
    template_path = tmp_path / "template.yaml"
    template_path.write_text(
        "\n".join(
            [
                "AWSTemplateFormatVersion: '2010-09-09'",
                "Resources:",
                "  MyBucket:",
                "    Type: AWS::S3::Bucket",
                "",
            ]
        ),
        encoding="utf-8",
    )

    store = SolutionKBStore(root_dir=str(tmp_path / "kb"))
    ingestor = SolutionKBIngestor(store=store)
    ingestor.ingest_path(str(template_path), include_body=True)
    items = store.list_all()
    assert items
    template_id = items[0].meta.template_id

    out_path = tmp_path / "exported.yaml"
    runner = CliRunner()
    result = runner.invoke(
        kb_app,
        [
            "export",
            "--template-id",
            str(template_id),
            "--out",
            str(out_path),
            "--kb-dir",
            str(store.root_dir),
        ],
    )
    assert result.exit_code == 0
    assert out_path.read_text(encoding="utf-8").startswith("AWSTemplateFormatVersion")
