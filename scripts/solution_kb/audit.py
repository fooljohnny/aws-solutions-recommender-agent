from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install pyyaml to run this script.") from exc

ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit solution KB manifests and asset coverage.")
    parser.add_argument(
        "--manifest",
        default="data/solution_kb/manifests/template_manifest.jsonl",
        help="Path to template_manifest.jsonl",
    )
    parser.add_argument(
        "--targets",
        default="data/solution_kb/targets.yaml",
        help="Path to targets.yaml (optional)",
    )
    return parser.parse_args()


def _resolve_path(value: str) -> Path:
    p = Path(value)
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()


def _load_manifest(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _load_targets(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _count_by_key(items: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        val = str(item.get(key) or "").strip() or "unknown"
        counts[val] = counts.get(val, 0) + 1
    return counts


def _file_exists(path_str: str) -> bool:
    if not path_str:
        return False
    p = Path(path_str)
    if not p.is_absolute():
        p = ROOT / p
    return p.exists()


def main() -> None:
    args = parse_args()
    manifest_path = _resolve_path(args.manifest)
    rows = _load_manifest(manifest_path)

    by_source = _count_by_key(rows, "source")
    by_mode = _count_by_key(rows, "diagram_mode")
    by_format = _count_by_key(rows, "diagram_format")

    missing_diagrams = sum(1 for r in rows if not _file_exists(str(r.get("diagram_path") or "")))
    missing_templates = sum(1 for r in rows if not _file_exists(str(r.get("template_path") or "")))

    report: Dict[str, Any] = {
        "total": len(rows),
        "by_source": by_source,
        "by_diagram_mode": by_mode,
        "by_diagram_format": by_format,
        "missing_diagram_files": missing_diagrams,
        "missing_template_files": missing_templates,
    }

    targets_path = _resolve_path(args.targets)
    targets = _load_targets(targets_path)
    source_targets = targets.get("source_targets") if isinstance(targets, dict) else {}
    if isinstance(source_targets, dict):
        delta: Dict[str, Any] = {}
        for src, target in source_targets.items():
            actual = by_source.get(src, 0)
            delta[src] = {"target": int(target), "actual": int(actual), "remaining": int(target) - int(actual)}
        report["targets"] = delta

    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
