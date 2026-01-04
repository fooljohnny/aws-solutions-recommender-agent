"""CLI commands for solution template knowledge base."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.table import Table
from uuid import UUID
from typing import Optional

from ..services.solution_kb.ingest import SolutionKBIngestor
from ..services.solution_kb.models import TemplateSource
from ..services.solution_kb.store_factory import get_solution_kb_store
from ..services.solution_kb.meta import parse_meta_file


app = typer.Typer(help="Solution template knowledge base (KB) utilities")
console = Console()


@app.command()
def ingest(
    path: str = typer.Argument(..., help="File or directory containing templates"),
    source: TemplateSource = typer.Option(TemplateSource.LOCAL, "--source", help="Template source label"),
    repository: str = typer.Option(None, "--repo", help="Repository identifier or URL"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (defaults to .solution_kb)"),
    max_files: int = typer.Option(2000, "--max-files", help="Max files to scan in a directory"),
):
    """Ingest CloudFormation templates (JSON/YAML) into the KB (Neo4j or local file)."""
    store = get_solution_kb_store(root_dir=kb_dir)
    ingestor = SolutionKBIngestor(store=store)
    stats = ingestor.ingest_path(path, source=source, repository=repository, max_files=max_files)
    console.print(
        f"[green]Ingest complete[/green] parsed={stats.parsed} skipped={stats.skipped} failed={stats.failed}"
    )


@app.command()
def search(
    query: str = typer.Argument(..., help="Keyword query"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (defaults to .solution_kb)"),
    limit: int = typer.Option(5, "--limit", help="Max results"),
):
    """Search the KB for templates."""
    store = get_solution_kb_store(root_dir=kb_dir)
    results = store.search(keywords=[query], limit=limit)
    if not results:
        console.print("[yellow]No results.[/yellow]")
        raise typer.Exit(code=0)

    table = Table(title="KB Search Results")
    table.add_column("template_id", style="dim")
    table.add_column("name")
    table.add_column("source")
    table.add_column("resource_types")
    table.add_column("parameters")

    for t in results:
        table.add_row(
            str(t.meta.template_id),
            t.meta.name or "",
            t.meta.source.value,
            ", ".join(t.resource_types[:8]),
            ", ".join([p.name for p in t.parameters[:6]]),
        )

    console.print(table)


@app.command("init-neo4j")
def init_neo4j():
    """Initialize Neo4j constraints/indexes for the KB graph.

    Requires env vars: NEO4J_URI, NEO4J_USER (optional), NEO4J_PASSWORD, NEO4J_DATABASE (optional)
    """
    from ..services.solution_kb.neo4j_store import Neo4jSolutionKBStore

    store = Neo4jSolutionKBStore.from_env()
    store.ensure_schema()
    console.print("[green]Neo4j KB schema initialized.[/green]")


@app.command("validate-meta")
def validate_meta(
    meta_path: str = typer.Argument(..., help="Path to kb.meta.yaml/yml/json"),
):
    """Validate an ops metadata file (kb.meta.*)."""
    from pathlib import Path

    spec = parse_meta_file(Path(meta_path))
    console.print("[green]Meta file is valid.[/green]")
    # Print a small summary for ops
    if spec.templates:
        console.print(f"[dim]Mode[/dim]: multi-template (templates={len(spec.templates)})")
    else:
        console.print("[dim]Mode[/dim]: single-template/default")


@app.command("annotate")
def annotate(
    template_id: str = typer.Option(..., "--template-id", help="Template UUID in KB/graph"),
    name: str = typer.Option(None, "--name", help="Override name"),
    description: str = typer.Option(None, "--description", help="Override description"),
    tags: str = typer.Option(None, "--tags", help="Comma-separated tags"),
    industries: str = typer.Option(None, "--industries", help="Comma-separated industries"),
    business_types: str = typer.Option(None, "--business-types", help="Comma-separated business types"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (local backend only)"),
):
    """Patch metadata for a template already in the KB (Neo4j or local file)."""
    store = get_solution_kb_store(root_dir=kb_dir)
    tid = UUID(template_id)

    def split_csv(s: Optional[str]):
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    ok = store.update_template_metadata(
        tid,
        name=name,
        description=description,
        tags=split_csv(tags),
        industries=split_csv(industries),
        business_types=split_csv(business_types),
    )
    if not ok:
        console.print(f"[red]Template not found:[/red] {tid}")
        raise typer.Exit(code=1)
    console.print("[green]Template metadata updated.[/green]")


@app.command("suggest-links")
def suggest_links(
    resource_type: str = typer.Option(..., "--resource-type", help="Resource type, e.g. AWS::Lambda::Function"),
    relation: str = typer.Option(
        "both",
        "--relation",
        help="Edge type: depends_on | references | both",
    ),
    direction: str = typer.Option(
        "out",
        "--direction",
        help="Direction: out (A->B) | in (X->A) | both",
    ),
    industries: str = typer.Option(None, "--industries", help="Comma-separated industries filter"),
    business_types: str = typer.Option(None, "--business-types", help="Comma-separated business types filter"),
    limit: int = typer.Option(10, "--limit", help="Max suggested target resource types"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (local backend only)"),
):
    """Suggest which resource types are most often connected to a given resource type."""
    store = get_solution_kb_store(root_dir=kb_dir)

    def split_csv(s: Optional[str]):
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    pairs = store.suggest_connected_resource_types(
        resource_type=resource_type,
        relation=relation,
        direction=direction,
        industries=split_csv(industries),
        business_types=split_csv(business_types),
        limit=limit,
    )
    if not pairs:
        console.print("[yellow]No suggestions (graph may be empty or missing resource bodies).[/yellow]")
        raise typer.Exit(code=0)

    table = Table(title="Most-likely connected resource types")
    table.add_column("source_type")
    table.add_column("target_type")
    table.add_column("count", justify="right")
    for tgt, cnt in pairs:
        table.add_row(resource_type, tgt, str(cnt))
    console.print(table)

