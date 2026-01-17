"""CLI commands for solution template knowledge base."""

from __future__ import annotations

import json
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from uuid import UUID, uuid4
from typing import Optional

from ..models.user_requirement import RequirementType, UserRequirement
from ..services.recommendation.solution_kb_recommendation import SolutionKBRecommendationService
from ..services.solution_kb.ingest import SolutionKBIngestor
from ..services.solution_kb.exporter import load_template_body
from ..services.solution_kb.models import TemplateSource
from ..services.solution_kb.retriever import SolutionTemplateRetriever
from ..services.solution_kb.suggester import suggest_next_resource_types
from ..services.solution_kb.store_factory import get_solution_kb_store
from ..services.solution_kb.meta import parse_meta_file
from ..services.solution_kb.ranking import HybridRanker, OnlineWeightLearner, WeightStore, RankWeights


app = typer.Typer(help="Solution template knowledge base (KB) utilities")
console = Console()


@app.command()
def ingest(
    path: str = typer.Argument(..., help="File or directory containing templates"),
    source: TemplateSource = typer.Option(TemplateSource.LOCAL, "--source", help="Template source label"),
    repository: str = typer.Option(None, "--repo", help="Repository identifier or URL"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (defaults to .solution_kb)"),
    max_files: int = typer.Option(2000, "--max-files", help="Max files to scan in a directory"),
    include_body: bool = typer.Option(
        False,
        "--include-body",
        help="Store raw template body for export (may increase KB size)",
    ),
):
    """Ingest CloudFormation templates (JSON/YAML) into the KB (Neo4j or local file)."""
    store = get_solution_kb_store(root_dir=kb_dir)
    ingestor = SolutionKBIngestor(store=store)
    stats = ingestor.ingest_path(
        path,
        source=source,
        repository=repository,
        max_files=max_files,
        include_body=include_body,
    )
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


@app.command("export")
def export_template(
    template_id: str = typer.Option(..., "--template-id", help="Template UUID in KB/graph"),
    out: str = typer.Option(None, "--out", help="Output path for template body (prints to stdout if omitted)"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (local backend only)"),
):
    """Export the raw template body (if stored or path is accessible)."""
    store = get_solution_kb_store(root_dir=kb_dir)
    tid = UUID(template_id)
    template = store.get(tid) if hasattr(store, "get") else None
    if not template:
        console.print(f"[red]Template not found:[/red] {tid}")
        raise typer.Exit(code=1)

    body = load_template_body(template)
    if not body:
        console.print(
            "[yellow]Template body not available. Re-ingest with --include-body or ensure path exists.[/yellow]"
        )
        raise typer.Exit(code=2)

    if out:
        out_path = Path(out)
        if (out_path.exists() and out_path.is_dir()) or not out_path.suffix:
            out_path = out_path / f"{template.meta.template_id}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body, encoding="utf-8")
        console.print(f"[green]Template exported:[/green] {out_path}")
        return

    console.print(body, markup=False, highlight=False)


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


@app.command("suggest-next")
def suggest_next(
    resource_types: str = typer.Option(None, "--resource-types", help="Comma-separated resource types"),
    template_id: str = typer.Option(None, "--template-id", help="Template UUID to derive resource types"),
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
    include_existing: bool = typer.Option(
        False,
        "--include-existing",
        help="Include resource types already present in the input set",
    ),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (local backend only)"),
):
    """Suggest next resource types given an existing set."""
    store = get_solution_kb_store(root_dir=kb_dir)

    def split_csv(s: Optional[str]):
        if not s:
            return None
        return [x.strip() for x in s.split(",") if x.strip()]

    types: list[str] = []
    if template_id:
        tid = UUID(template_id)
        template = store.get(tid) if hasattr(store, "get") else None
        if not template:
            console.print(f"[red]Template not found:[/red] {tid}")
            raise typer.Exit(code=1)
        types.extend(list(template.resource_types or []))

    types.extend(split_csv(resource_types) or [])
    if not types:
        console.print("[red]Provide --resource-types or --template-id to suggest next resources.[/red]")
        raise typer.Exit(code=1)

    pairs = suggest_next_resource_types(
        store,
        types,
        relation=relation,
        direction=direction,
        industries=split_csv(industries),
        business_types=split_csv(business_types),
        limit=limit,
        exclude_present=not include_existing,
    )
    if not pairs:
        console.print("[yellow]No suggestions (graph may be empty or missing resource bodies).[/yellow]")
        raise typer.Exit(code=0)

    table = Table(title="Suggested next resource types")
    table.add_column("target_type")
    table.add_column("count", justify="right")
    for tgt, cnt in pairs:
        table.add_row(tgt, str(cnt))
    console.print(table)


@app.command("recommend")
def recommend(
    query: str = typer.Argument(..., help="Natural language query for solution templates"),
    limit: int = typer.Option(3, "--limit", help="Max recommended templates"),
    no_clarify: bool = typer.Option(False, "--no-clarify", help="Skip clarification questions"),
    export: str = typer.Option(None, "--export", help="Export top template to a file or directory"),
    show_diagram: bool = typer.Option(False, "--diagram", help="Print Mermaid diagrams for results"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (local backend only)"),
):
    """Recommend mature templates from the KB using a natural language query."""
    store = get_solution_kb_store(root_dir=kb_dir)
    retriever = SolutionTemplateRetriever(store=store)
    recommender = SolutionKBRecommendationService(retriever=retriever)

    reqs = [
        UserRequirement(
            session_id=uuid4(),
            requirement_type=RequirementType.CONSTRAINT,
            requirement_value=query,
            confidence=0.9,
        )
    ]

    result = recommender.recommend(
        reqs,
        clarification_rounds_used=2 if no_clarify else 0,
        max_clarification_rounds=0 if no_clarify else 2,
        limit=limit,
    )

    if result.needs_clarification:
        console.print("[yellow]Need more details to refine recommendations:[/yellow]")
        for idx, q in enumerate(result.clarification_questions, start=1):
            console.print(f"{idx}. {q}")
        if result.assumptions:
            console.print("\n[dim]Default assumptions if you skip details:[/dim]")
            for a in result.assumptions:
                console.print(f"- {a}")
        raise typer.Exit(code=0)

    if not result.recommended:
        console.print("[yellow]No matching templates found.[/yellow]")
        raise typer.Exit(code=0)

    if result.fallback_top_by_usage:
        console.print("[dim]No strong match; showing top templates by usage.[/dim]")

    table = Table(title="Recommended templates")
    table.add_column("#", justify="right")
    table.add_column("template_id", style="dim")
    table.add_column("name")
    table.add_column("source")
    table.add_column("resource_types")
    table.add_column("description")

    for idx, rec in enumerate(result.recommended, start=1):
        meta = rec.template.meta
        source_val = meta.source.value if hasattr(meta.source, "value") else str(meta.source)
        table.add_row(
            str(idx),
            str(meta.template_id),
            meta.name or "",
            source_val,
            ", ".join(rec.template.resource_types[:8]),
            (meta.description or "")[:120],
        )
    console.print(table)

    if show_diagram:
        for idx, rec in enumerate(result.recommended, start=1):
            console.print(f"\n[bold]Mermaid diagram for #{idx}[/bold]")
            console.print(rec.diagram_mermaid, markup=False)

    if export:
        top = result.recommended[0].template
        body = load_template_body(top)
        if not body:
            console.print(
                "[yellow]Template body not available. Re-ingest with --include-body or ensure path exists.[/yellow]"
            )
            raise typer.Exit(code=2)

        out_path = Path(export)
        if (out_path.exists() and out_path.is_dir()) or not out_path.suffix:
            out_path = out_path / f"{top.meta.template_id}.yaml"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(body, encoding="utf-8")
        console.print(f"[green]Template exported:[/green] {out_path}")


@app.command("show-weights")
def show_weights(kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (for local weight file)")):
    """Show current ranking weights (for hybrid ranker)."""
    store = WeightStore(root_dir=kb_dir)
    w = store.load()
    console.print_json(data=w.__dict__)


@app.command("reset-weights")
def reset_weights(kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (for local weight file)")):
    """Reset ranking weights back to defaults."""
    store = WeightStore(root_dir=kb_dir)
    store.save(RankWeights())
    console.print("[green]Weights reset.[/green]")


@app.command("feedback")
def feedback(
    chosen_template_id: str = typer.Option(..., "--chosen", help="Chosen template UUID"),
    rejected_template_id: str = typer.Option(..., "--rejected", help="Rejected template UUID"),
    query: str = typer.Option(..., "--query", help="Original user description"),
    kb_dir: str = typer.Option(None, "--kb-dir", help="KB directory (for local weight file)"),
):
    """Provide pairwise feedback to learn ranking weights (chosen > rejected)."""
    from uuid import uuid4
    from ..models.user_requirement import UserRequirement, RequirementType

    # Convert query into a minimal requirement list (learning uses it as query text).
    reqs = [
        UserRequirement(
            session_id=uuid4(),
            requirement_type=RequirementType.CONSTRAINT,
            requirement_value=query,
            confidence=0.9,
        )
    ]

    store = get_solution_kb_store(root_dir=kb_dir)
    chosen_id = UUID(chosen_template_id)
    rejected_id = UUID(rejected_template_id)

    chosen = store.get(chosen_id) if hasattr(store, "get") else None
    rejected = store.get(rejected_id) if hasattr(store, "get") else None
    if not chosen or not rejected:
        console.print("[red]Could not load chosen/rejected templates from KB.[/red]")
        raise typer.Exit(code=1)

    ws = WeightStore(root_dir=kb_dir)
    ranker = HybridRanker(weight_store=ws)
    learner = OnlineWeightLearner(ranker)
    w = learner.update_pair(requirements=reqs, chosen=chosen, rejected=rejected, keywords=[query])
    console.print("[green]Weights updated.[/green]")
    console.print_json(data=w.__dict__)

