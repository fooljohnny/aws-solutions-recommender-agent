"""CLI commands for solution template knowledge base."""

from __future__ import annotations

import json
import typer
from rich.console import Console
from rich.table import Table

from ..services.solution_kb.ingest import SolutionKBIngestor
from ..services.solution_kb.models import TemplateSource
from ..services.solution_kb.store import SolutionKBStore


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
    """Ingest CloudFormation templates (JSON/YAML) into the local KB."""
    store = SolutionKBStore(root_dir=kb_dir) if kb_dir else SolutionKBStore()
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
    """Search the local KB for templates."""
    store = SolutionKBStore(root_dir=kb_dir) if kb_dir else SolutionKBStore()
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

