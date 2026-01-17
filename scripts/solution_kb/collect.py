from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install pyyaml to run this script.") from exc

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.services.diagram.renderer import DiagramRenderer
from src.services.diagram.template_generator import TemplateDiagramGenerator
from src.services.solution_kb.ingest import SolutionKBIngestor, IngestStats
from src.services.solution_kb.models import TemplateExtract, TemplateSource
from src.services.solution_kb.store_factory import get_solution_kb_store

DEFAULT_DIAGRAM_NAMES = ["architecture", "diagram", "overview"]
DEFAULT_DIAGRAM_EXTS = [".svg", ".png", ".jpg", ".jpeg", ".webp"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect solution templates and diagrams into a local KB.")
    parser.add_argument("--config", required=True, help="Path to sources.yaml config")
    parser.add_argument("--kb-dir", default=None, help="Override KB directory")
    parser.add_argument("--output-dir", default=None, help="Override output directory")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files or update KB store")
    return parser.parse_args()


def _resolve_path(value: str) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()


def _rel(path: Optional[Path]) -> str:
    if not path:
        return ""
    try:
        return str(path.relative_to(ROOT))
    except Exception:
        return str(path)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _normalize_mode(mode: str) -> str:
    val = (mode or "").strip().lower()
    if val in {"repo", "from_repo"}:
        return "from_repo"
    if val in {"none", "skip"}:
        return "none"
    return "auto"


def _normalize_format(fmt: str) -> str:
    val = (fmt or "").strip().lower()
    if val in {"svg", "png", "mmd", "mermaid"}:
        return "mmd" if val == "mermaid" else val
    return "mmd"


def _load_config(path: Path) -> Dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Config must be a mapping.")
    return data


def _find_repo_diagram(template_path: Path, diagram_subdir: Optional[str]) -> Optional[Path]:
    base_dir = template_path.parent
    stem = template_path.stem
    candidates: List[Path] = []

    for ext in DEFAULT_DIAGRAM_EXTS:
        candidates.append(base_dir / f"{stem}{ext}")
    for name in DEFAULT_DIAGRAM_NAMES:
        for ext in DEFAULT_DIAGRAM_EXTS:
            candidates.append(base_dir / f"{name}{ext}")

    if diagram_subdir:
        sub = (base_dir / diagram_subdir).resolve()
        for ext in DEFAULT_DIAGRAM_EXTS:
            candidates.append(sub / f"{stem}{ext}")
        for name in DEFAULT_DIAGRAM_NAMES:
            for ext in DEFAULT_DIAGRAM_EXTS:
                candidates.append(sub / f"{name}{ext}")

    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def _copy_template(
    template: TemplateExtract,
    output_dir: Path,
    *,
    dry_run: bool,
) -> Tuple[str, str]:
    template_id = str(template.meta.template_id)
    src_path = Path(template.meta.path) if template.meta.path else None
    ext = (src_path.suffix if src_path else ".yaml") or ".yaml"
    dest = output_dir / "templates" / f"{template_id}{ext}"
    _ensure_dir(dest.parent)

    if dry_run:
        return _rel(dest), _rel(src_path)

    if src_path and src_path.exists():
        dest.write_bytes(src_path.read_bytes())
    elif template.meta.template_body:
        dest.write_text(template.meta.template_body, encoding="utf-8")
    else:
        return "", _rel(src_path)

    return _rel(dest), _rel(src_path)


def _generate_diagram(
    template: TemplateExtract,
    output_dir: Path,
    diagram_format: str,
    renderer: DiagramRenderer,
    *,
    dry_run: bool,
) -> Tuple[str, str]:
    template_id = str(template.meta.template_id)
    generator = TemplateDiagramGenerator()
    mermaid = generator.generate_mermaid(template)

    if diagram_format == "mmd":
        dest = output_dir / "diagrams" / f"{template_id}.mmd"
        _ensure_dir(dest.parent)
        if not dry_run:
            dest.write_text(mermaid, encoding="utf-8")
        return _rel(dest), "mmd"

    if diagram_format == "svg":
        dest = output_dir / "diagrams" / f"{template_id}.svg"
        _ensure_dir(dest.parent)
        if not dry_run:
            content = renderer.render_svg(mermaid)
            dest.write_text(content, encoding="utf-8")
        return _rel(dest), "svg"

    if diagram_format == "png":
        dest = output_dir / "diagrams" / f"{template_id}.png"
        _ensure_dir(dest.parent)
        if not dry_run:
            try:
                content = renderer.render_png(mermaid)
                dest.write_bytes(content)
                return _rel(dest), "png"
            except Exception:
                pass

    # fallback to Mermaid source if rendering fails
    dest = output_dir / "diagrams" / f"{template_id}.mmd"
    _ensure_dir(dest.parent)
    if not dry_run:
        dest.write_text(mermaid, encoding="utf-8")
    return _rel(dest), "mmd"


def _collect_source(
    source_cfg: Dict[str, Any],
    defaults: Dict[str, Any],
    *,
    kb_dir: Optional[str],
    output_dir: Optional[str],
    dry_run: bool,
) -> Tuple[List[TemplateExtract], IngestStats, List[Dict[str, Any]]]:
    source_name = str(source_cfg.get("source") or defaults.get("source") or "local").strip()
    source_enum = TemplateSource(source_name)

    local_path_raw = source_cfg.get("local_path") or ""
    if not local_path_raw:
        raise ValueError("local_path is required for each source.")
    local_path = _resolve_path(local_path_raw)
    if not local_path.exists():
        return [], IngestStats(parsed=0, failed=0, skipped=0), []

    repo = source_cfg.get("repository") or defaults.get("repository")
    include_body = bool(source_cfg.get("include_body", defaults.get("include_body", False)))
    copy_templates = bool(source_cfg.get("copy_templates", defaults.get("copy_templates", True)))
    max_files = int(source_cfg.get("max_files", defaults.get("max_files", 2000)))
    diagram_mode = _normalize_mode(str(source_cfg.get("diagram_mode", defaults.get("diagram_mode", "auto"))))
    diagram_format = _normalize_format(str(source_cfg.get("diagram_format", defaults.get("diagram_format", "mmd"))))
    diagram_subdir = str(source_cfg.get("diagram_subdir", defaults.get("diagram_subdir", "")) or "")

    store = get_solution_kb_store(root_dir=kb_dir or defaults.get("kb_dir"))
    ingestor = SolutionKBIngestor(store=store)
    extracts, stats = ingestor.collect_from_path(
        str(local_path),
        source=source_enum,
        repository=repo,
        max_files=max_files,
        include_body=include_body,
    )

    if not dry_run and extracts:
        store.upsert_many(extracts)

    out_dir = _resolve_path(output_dir or defaults.get("output_dir") or "data/solution_kb")
    _ensure_dir(out_dir)

    renderer = DiagramRenderer()
    manifest_entries: List[Dict[str, Any]] = []

    for ex in extracts:
        entry: Dict[str, Any] = {}
        template_path, template_source_path = ("", "")
        if copy_templates:
            template_path, template_source_path = _copy_template(ex, out_dir, dry_run=dry_run)
        else:
            template_source_path = _rel(Path(ex.meta.path)) if ex.meta.path else ""
            template_path = template_source_path

        diagram_path = ""
        diagram_format_used = "none"
        diagram_source_path = ""
        diagram_mode_used = "missing"

        if diagram_mode != "none":
            repo_diagram = None
            if ex.meta.path:
                repo_diagram = _find_repo_diagram(Path(ex.meta.path), diagram_subdir or None)
            if repo_diagram:
                ext = repo_diagram.suffix.lower() or ".svg"
                dest = out_dir / "diagrams" / f"{ex.meta.template_id}{ext}"
                _ensure_dir(dest.parent)
                if not dry_run:
                    dest.write_bytes(repo_diagram.read_bytes())
                diagram_path = _rel(dest)
                diagram_format_used = ext.lstrip(".")
                diagram_source_path = _rel(repo_diagram)
                diagram_mode_used = "repo"
            elif diagram_mode == "auto":
                diagram_path, diagram_format_used = _generate_diagram(
                    ex, out_dir, diagram_format, renderer, dry_run=dry_run
                )
                diagram_mode_used = "auto"

        entry.update(
            {
                "template_id": str(ex.meta.template_id),
                "template_name": ex.meta.name or "",
                "template_kind": str(ex.meta.kind.value if hasattr(ex.meta.kind, "value") else ex.meta.kind),
                "source": str(source_enum.value),
                "repository": str(repo or ""),
                "template_path": template_path,
                "template_source_path": template_source_path,
                "diagram_path": diagram_path,
                "diagram_format": diagram_format_used,
                "diagram_mode": diagram_mode_used,
                "diagram_source_path": diagram_source_path,
                "resource_types": list(ex.resource_types or []),
                "tags": list(ex.meta.tags or []),
                "industries": list(ex.meta.industries or []),
                "business_types": list(ex.meta.business_types or []),
                "collected_at": ex.meta.collected_at.isoformat()
                if ex.meta.collected_at
                else datetime.now(timezone.utc).isoformat(),
            }
        )
        manifest_entries.append(entry)

    return extracts, stats, manifest_entries


def _load_manifest(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    items: Dict[str, Dict[str, Any]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except Exception:
            continue
        template_id = str(data.get("template_id") or "")
        if template_id:
            items[template_id] = data
    return items


def _write_manifest(path: Path, items: Dict[str, Dict[str, Any]], *, dry_run: bool) -> None:
    _ensure_dir(path.parent)
    if dry_run:
        return
    lines = [json.dumps(v, ensure_ascii=True) for v in items.values()]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> None:
    args = parse_args()
    config_path = _resolve_path(args.config)
    config = _load_config(config_path)
    defaults = dict(config.get("defaults") or {})
    sources = list(config.get("sources") or [])

    manifest_path = _resolve_path(
        defaults.get("manifest_path", "data/solution_kb/manifests/template_manifest.jsonl")
    )
    existing = _load_manifest(manifest_path)

    total_parsed = total_skipped = total_failed = 0
    for src in sources:
        extracts, stats, manifest_entries = _collect_source(
            src,
            defaults,
            kb_dir=args.kb_dir,
            output_dir=args.output_dir,
            dry_run=args.dry_run,
        )
        total_parsed += stats.parsed
        total_skipped += stats.skipped
        total_failed += stats.failed
        for entry in manifest_entries:
            existing[entry["template_id"]] = entry

    _write_manifest(manifest_path, existing, dry_run=args.dry_run)

    summary = {
        "parsed": total_parsed,
        "skipped": total_skipped,
        "failed": total_failed,
        "manifest_entries": len(existing),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
