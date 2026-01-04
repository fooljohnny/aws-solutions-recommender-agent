"""Ingestion pipeline for IaC templates into the solution KB."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from .cfn_parser import CloudFormationTemplateParser, CloudFormationParseError
from .meta import find_meta_file_for_template, parse_meta_file, pick_annotation_for_template
from .models import TemplateExtract, TemplateSource
from .store import SolutionKBStore
from .store_factory import get_solution_kb_store


@dataclass(frozen=True)
class IngestStats:
    parsed: int
    failed: int
    skipped: int


class SolutionKBIngestor:
    """Collects templates from local paths and stores normalized extracts."""

    def __init__(self, store: Optional[SolutionKBStore] = None):
        self.store = store or get_solution_kb_store()
        self.cfn_parser = CloudFormationTemplateParser()

    def ingest_path(
        self,
        path: str,
        *,
        source: TemplateSource = TemplateSource.LOCAL,
        repository: Optional[str] = None,
        max_files: int = 2000,
    ) -> IngestStats:
        root = Path(path)
        if root.is_file():
            extracts, stats = self._ingest_files([root], source=source, repository=repository)
            self.store.upsert_many(extracts)
            return stats

        if not root.exists():
            return IngestStats(parsed=0, failed=0, skipped=0)

        files: List[Path] = []
        for ext in ("*.yaml", "*.yml", "*.json"):
            files.extend(root.rglob(ext))
        files = files[:max_files]

        extracts, stats = self._ingest_files(files, source=source, repository=repository)
        if extracts:
            self.store.upsert_many(extracts)
        return stats

    def _ingest_files(
        self,
        files: Iterable[Path],
        *,
        source: TemplateSource,
        repository: Optional[str],
    ) -> tuple[List[TemplateExtract], IngestStats]:
        extracts: List[TemplateExtract] = []
        parsed = failed = skipped = 0

        for fp in files:
            # Heuristic: skip huge non-template JSON/YAML files
            try:
                if fp.stat().st_size > 2_000_000:
                    skipped += 1
                    continue
            except Exception:
                pass

            try:
                ex = self.cfn_parser.parse_file(str(fp), source=source, repository=repository)
                # Heuristic: must have Resources or Parameters to be useful
                if not ex.resources and not ex.parameters:
                    skipped += 1
                    continue

                # Merge ops annotations from kb.meta.* if present
                meta_file = find_meta_file_for_template(fp)
                if meta_file:
                    meta_spec = parse_meta_file(meta_file)
                    ann = pick_annotation_for_template(meta_spec, fp)
                    if ann:
                        if ann.name:
                            ex.meta.name = ann.name
                        if ann.description:
                            ex.meta.description = ann.description
                        if ann.source:
                            ex.meta.source = ann.source
                        if ann.repository:
                            ex.meta.repository = ann.repository
                        if ann.tags:
                            ex.meta.tags = sorted(set(ex.meta.tags).union(ann.tags))
                        if ann.industries:
                            ex.meta.industries = sorted(set(ex.meta.industries).union(ann.industries))
                        if ann.business_types:
                            ex.meta.business_types = sorted(
                                set(ex.meta.business_types).union(ann.business_types)
                            )

                extracts.append(ex)
                parsed += 1
            except CloudFormationParseError:
                # Not a CloudFormation template; could be unrelated YAML/JSON.
                skipped += 1
            except Exception:
                failed += 1

        return extracts, IngestStats(parsed=parsed, failed=failed, skipped=skipped)

