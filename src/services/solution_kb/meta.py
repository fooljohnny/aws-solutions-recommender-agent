"""Operations metadata parsing for solution templates.

Supports a convention file placed next to templates:
- kb.meta.yaml / kb.meta.yml / kb.meta.json

Two modes:
1) Single-template mode (top-level fields apply to the local template file)
2) Multi-template mode:
   templates:
     - path: template-a.yaml
       name: ...
       tags: [...]
     - path: nested/template-b.yaml
       ...
   default:
     tags: [...]
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from pydantic import BaseModel, Field

from .models import TemplateSource


class TemplateMetaAnnotation(BaseModel):
    """Annotation fields that ops can maintain."""

    path: Optional[str] = Field(
        default=None,
        description="Relative path of the template file (only in multi-template mode).",
    )
    name: Optional[str] = None
    description: Optional[str] = None
    source: Optional[TemplateSource] = None
    repository: Optional[str] = None
    industries: List[str] = Field(default_factory=list)
    business_types: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class MetaFileSpec(BaseModel):
    """A meta file that can optionally cover multiple templates."""

    default: Optional[TemplateMetaAnnotation] = None
    templates: List[TemplateMetaAnnotation] = Field(default_factory=list)


def find_meta_file_for_template(template_path: Path) -> Optional[Path]:
    """Search for kb.meta.* in the template's directory."""
    parent = template_path.parent
    for name in ("kb.meta.yaml", "kb.meta.yml", "kb.meta.json"):
        p = parent / name
        if p.exists() and p.is_file():
            return p
    return None


def parse_meta_file(path: Path) -> MetaFileSpec:
    """Parse kb.meta.yaml/yml/json into MetaFileSpec."""
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        if yaml is None:
            raise ValueError("Parsing kb.meta.yaml requires PyYAML (pyyaml).")
        data = yaml.safe_load(text)

    if data is None:
        return MetaFileSpec()

    # If it looks like a single-template annotation, wrap it as default.
    if isinstance(data, dict) and "templates" not in data and "default" not in data:
        return MetaFileSpec(default=TemplateMetaAnnotation.model_validate(data))

    return MetaFileSpec.model_validate(data)


def pick_annotation_for_template(meta: MetaFileSpec, template_path: Path) -> Optional[TemplateMetaAnnotation]:
    """Return the best annotation for a given template path."""
    # Multi-template mode: match by relative path.
    rel = None
    try:
        rel = str(template_path.relative_to(template_path.parent))
    except Exception:
        rel = template_path.name

    for t in meta.templates:
        if t.path and Path(t.path).as_posix() == Path(rel).as_posix():
            return _merge_annotations(meta.default, t)

    # Single-template mode: meta.default only.
    if meta.default:
        return meta.default
    return None


def _merge_annotations(
    base: Optional[TemplateMetaAnnotation],
    override: Optional[TemplateMetaAnnotation],
) -> TemplateMetaAnnotation:
    if base is None:
        return override or TemplateMetaAnnotation()
    if override is None:
        return base

    merged = TemplateMetaAnnotation.model_validate(base.model_dump())
    for field in ("name", "description", "source", "repository"):
        v = getattr(override, field)
        if v is not None and v != "":
            setattr(merged, field, v)
    merged.tags = sorted({*(base.tags or []), *(override.tags or [])})
    merged.industries = sorted({*(base.industries or []), *(override.industries or [])})
    merged.business_types = sorted({*(base.business_types or []), *(override.business_types or [])})
    return merged

