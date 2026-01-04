"""CloudFormation template parsing and normalization.

Supports JSON and YAML templates. Extracts:
- Parameters (spec, constraints)
- Resources (type, properties, DependsOn, references)
- Outputs (value, exports, references)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import json

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from .models import (
    OutputSpec,
    ParameterSpec,
    ResourceSpec,
    TemplateExtract,
    TemplateKind,
    TemplateMetadata,
    TemplateSource,
)


class CloudFormationParseError(ValueError):
    """Raised when a CloudFormation template cannot be parsed."""


@dataclass(frozen=True)
class CloudFormationParseResult:
    """Raw parse result before normalization."""

    document: Dict[str, Any]
    format: str  # "json" | "yaml"


class CloudFormationTemplateParser:
    """Parses CloudFormation JSON/YAML templates and normalizes into TemplateExtract."""

    def parse_text(
        self,
        text: str,
        *,
        source: TemplateSource = TemplateSource.LOCAL,
        name: str = "",
        repository: Optional[str] = None,
        path: Optional[str] = None,
    ) -> TemplateExtract:
        raw = self._parse_raw(text)
        meta = TemplateMetadata(
            kind=TemplateKind.CLOUDFORMATION,
            source=source,
            name=name,
            description=str(raw.document.get("Description", "") or ""),
            repository=repository,
            path=path,
        )
        return self._normalize(raw.document, meta)

    def parse_file(
        self,
        file_path: str,
        *,
        source: TemplateSource = TemplateSource.LOCAL,
        repository: Optional[str] = None,
    ) -> TemplateExtract:
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
        name = file_path.split("/")[-1]
        return self.parse_text(text, source=source, name=name, repository=repository, path=file_path)

    def _parse_raw(self, text: str) -> CloudFormationParseResult:
        # Try JSON first (fast and unambiguous).
        try:
            doc = json.loads(text)
            if isinstance(doc, dict):
                return CloudFormationParseResult(document=doc, format="json")
        except Exception:
            pass

        if yaml is None:
            raise CloudFormationParseError(
                "YAML parsing requires PyYAML. Install 'pyyaml' to parse .yaml/.yml templates."
            )

        try:
            doc = yaml.safe_load(text)
            if not isinstance(doc, dict):
                raise CloudFormationParseError("Template YAML root must be a mapping/object.")
            return CloudFormationParseResult(document=doc, format="yaml")
        except CloudFormationParseError:
            raise
        except Exception as e:
            raise CloudFormationParseError(f"Failed to parse template as JSON or YAML: {e}") from e

    def _normalize(self, doc: Dict[str, Any], meta: TemplateMetadata) -> TemplateExtract:
        parameters = self._extract_parameters(doc.get("Parameters") or {})
        resources = self._extract_resources(doc.get("Resources") or {})
        outputs = self._extract_outputs(doc.get("Outputs") or {})

        # Denormalized resource types for retrieval.
        resource_types = sorted({r.type for r in resources})

        # Augment meta tags from template metadata if present.
        template_tags = self._extract_template_tags(doc.get("Metadata"))
        meta.tags = sorted(set(meta.tags).union(template_tags))

        return TemplateExtract(
            meta=meta,
            parameters=parameters,
            resources=resources,
            outputs=outputs,
            resource_types=resource_types,
        )

    def _extract_parameters(self, params: Dict[str, Any]) -> List[ParameterSpec]:
        out: List[ParameterSpec] = []
        if not isinstance(params, dict):
            return out
        for name, spec in params.items():
            if not isinstance(spec, dict):
                continue
            out.append(
                ParameterSpec(
                    name=name,
                    type=spec.get("Type"),
                    default=spec.get("Default"),
                    description=spec.get("Description"),
                    allowed_values=spec.get("AllowedValues"),
                    allowed_pattern=spec.get("AllowedPattern"),
                    min_length=spec.get("MinLength"),
                    max_length=spec.get("MaxLength"),
                    min_value=spec.get("MinValue"),
                    max_value=spec.get("MaxValue"),
                    constraint_description=spec.get("ConstraintDescription"),
                    no_echo=spec.get("NoEcho"),
                )
            )
        return out

    def _extract_resources(self, resources: Dict[str, Any]) -> List[ResourceSpec]:
        out: List[ResourceSpec] = []
        if not isinstance(resources, dict):
            return out

        for logical_id, spec in resources.items():
            if not isinstance(spec, dict):
                continue
            r_type = spec.get("Type")
            if not isinstance(r_type, str) or not r_type:
                continue

            depends = spec.get("DependsOn") or []
            if isinstance(depends, str):
                depends_on = [depends]
            elif isinstance(depends, list):
                depends_on = [d for d in depends if isinstance(d, str)]
            else:
                depends_on = []

            properties = spec.get("Properties") or {}
            if not isinstance(properties, dict):
                properties = {}

            references = sorted(self._find_references(spec))

            out.append(
                ResourceSpec(
                    logical_id=logical_id,
                    type=r_type,
                    properties=properties,
                    depends_on=depends_on,
                    references=references,
                )
            )
        return out

    def _extract_outputs(self, outputs: Dict[str, Any]) -> List[OutputSpec]:
        out: List[OutputSpec] = []
        if not isinstance(outputs, dict):
            return out
        for name, spec in outputs.items():
            if not isinstance(spec, dict):
                continue
            value = spec.get("Value")
            export = spec.get("Export") or {}
            export_name = export.get("Name") if isinstance(export, dict) else None
            references = sorted(self._find_references(spec))
            out.append(
                OutputSpec(
                    name=name,
                    description=spec.get("Description"),
                    value=value,
                    export_name=export_name,
                    references=references,
                )
            )
        return out

    def _find_references(self, obj: Any) -> Set[str]:
        """Find referenced logical IDs via common intrinsic functions.

        Heuristic extraction:
        - Ref: "LogicalId"
        - Fn::GetAtt: ["LogicalId", "Attr"] or "LogicalId.Attr"
        - Fn::Sub: scans ${LogicalId} and ${LogicalId.Attr}
        - Fn::ImportValue / Fn::Join: recurse into args
        """

        refs: Set[str] = set()

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                # Short-form tags (YAML) may appear as {"Ref": ...}, etc.
                if "Ref" in node and isinstance(node["Ref"], str):
                    refs.add(node["Ref"])
                if "Fn::GetAtt" in node:
                    v = node["Fn::GetAtt"]
                    if isinstance(v, list) and v and isinstance(v[0], str):
                        refs.add(v[0])
                    elif isinstance(v, str) and "." in v:
                        refs.add(v.split(".", 1)[0])
                if "Fn::Sub" in node:
                    sub_val = node["Fn::Sub"]
                    if isinstance(sub_val, str):
                        refs.update(self._scan_sub_placeholders(sub_val))
                    elif isinstance(sub_val, list) and sub_val and isinstance(sub_val[0], str):
                        refs.update(self._scan_sub_placeholders(sub_val[0]))
                        # mapping substitutions may reference Ref/GetAtt too
                        if len(sub_val) > 1:
                            walk(sub_val[1])
                # generic recursion
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, str):
                # sometimes Sub strings appear outside explicit Fn::Sub in YAML
                if "${" in node:
                    refs.update(self._scan_sub_placeholders(node))

        walk(obj)
        return refs

    def _scan_sub_placeholders(self, s: str) -> Set[str]:
        # Very small placeholder scanner: ${X} or ${X.Y}
        out: Set[str] = set()
        i = 0
        while True:
            start = s.find("${", i)
            if start == -1:
                break
            end = s.find("}", start + 2)
            if end == -1:
                break
            expr = s[start + 2 : end].strip()
            if expr:
                # ignore pseudo parameters like AWS::Region
                if not expr.startswith("AWS::"):
                    out.add(expr.split(".", 1)[0])
            i = end + 1
        return out

    def _extract_template_tags(self, metadata: Any) -> List[str]:
        if not isinstance(metadata, dict):
            return []
        tags: Set[str] = set()
        # Common patterns:
        # - Metadata: { Tags: ["foo","bar"] }
        # - Metadata: { "AWS::CloudFormation::Interface": {...} } (ignore)
        raw = metadata.get("Tags") or metadata.get("tags")
        if isinstance(raw, list):
            for t in raw:
                if isinstance(t, str) and t.strip():
                    tags.add(t.strip())
        elif isinstance(raw, str) and raw.strip():
            tags.add(raw.strip())
        return sorted(tags)

