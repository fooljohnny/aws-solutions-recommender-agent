"""Helpers for exporting stored templates from the KB."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .models import TemplateExtract


def load_template_body(template: TemplateExtract) -> Optional[str]:
    """Return raw template body if available (inline or from path)."""
    body = (template.meta.template_body or "").strip()
    if body:
        return template.meta.template_body

    path = (template.meta.path or "").strip()
    if not path:
        return None

    fp = Path(path)
    if not fp.is_file():
        return None

    try:
        return fp.read_text(encoding="utf-8")
    except Exception:
        return None
