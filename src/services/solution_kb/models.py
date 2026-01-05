"""Data models for solution template knowledge base."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class TemplateKind(str, Enum):
    """Type of IaC template."""

    CLOUDFORMATION = "cloudformation"
    TERRAFORM = "terraform"
    UNKNOWN = "unknown"


class TemplateSource(str, Enum):
    """Where the template came from (used for ranking/trust)."""

    AWS_QUICKSTART = "aws_quickstart"
    AWS_SOLUTIONS = "aws_solutions"
    AWS_SAR = "aws_sar"
    AWS_SAMPLES = "aws_samples"
    TERRAFORM_AWS_MODULES = "terraform_aws_modules"
    AWS_IA = "aws_ia"
    COMMUNITY = "community"
    LOCAL = "local"


class GraphNodeType(str, Enum):
    TEMPLATE = "template"
    RESOURCE = "resource"
    PARAMETER = "parameter"
    OUTPUT = "output"
    TAG = "tag"
    INDUSTRY = "industry"
    BUSINESS_TYPE = "business_type"


class GraphEdgeType(str, Enum):
    CONTAINS = "contains"
    REFERENCES = "references"
    DEPENDS_ON = "depends_on"
    HAS_TAG = "has_tag"
    HAS_INDUSTRY = "has_industry"
    HAS_BUSINESS_TYPE = "has_business_type"


class TemplateMetadata(BaseModel):
    """High-level metadata for a template document."""

    template_id: UUID = Field(default_factory=uuid4)
    kind: TemplateKind = Field(default=TemplateKind.UNKNOWN)
    source: TemplateSource = Field(default=TemplateSource.LOCAL)
    name: str = Field(default="", description="Human-friendly name")
    description: str = Field(default="", description="Template description, if any")
    repository: Optional[str] = Field(default=None, description="Repo identifier or URL")
    path: Optional[str] = Field(default=None, description="Local path or source path")
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    industries: List[str] = Field(default_factory=list)
    business_types: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    usage_count: int = Field(
        default=0,
        ge=0,
        description="Optional popularity/usage metric used for fallback recommendations.",
    )
    # Optional embeddings for semantic retrieval
    embedding: Optional[List[float]] = Field(default=None, description="Vector embedding for template search text")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model identifier")


class ParameterSpec(BaseModel):
    """CloudFormation-like parameter spec (normalized)."""

    name: str
    type: Optional[str] = None
    default: Optional[Any] = None
    description: Optional[str] = None
    allowed_values: Optional[List[Any]] = None
    allowed_pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    constraint_description: Optional[str] = None
    no_echo: Optional[bool] = None


class ResourceSpec(BaseModel):
    """CloudFormation-like resource spec (normalized)."""

    logical_id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list, description="Logical IDs referenced via Ref/GetAtt/etc.")


class OutputSpec(BaseModel):
    """CloudFormation-like output spec (normalized)."""

    name: str
    description: Optional[str] = None
    value: Optional[Any] = None
    # Export name may be an intrinsic function (e.g., Fn::Sub), so keep as Any.
    export_name: Optional[Any] = None
    references: List[str] = Field(default_factory=list)


class TemplateExtract(BaseModel):
    """Normalized extracted representation used for indexing and KG building."""

    meta: TemplateMetadata
    parameters: List[ParameterSpec] = Field(default_factory=list)
    resources: List[ResourceSpec] = Field(default_factory=list)
    outputs: List[OutputSpec] = Field(default_factory=list)

    # Convenience fields for retrieval (denormalized).
    resource_types: List[str] = Field(default_factory=list)

