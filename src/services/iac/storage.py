"""IaC artifact storage and URL generation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from ...models.architecture_recommendation import ArchitectureRecommendation


class IaCStorage:
    """Stores IaC templates on disk and returns a stable download URL."""

    def __init__(self, storage_path: Optional[str] = None, base_url: Optional[str] = None):
        self.storage_path = Path(storage_path or "./iac")
        self.base_url = base_url or "/iac"
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_cloudformation(self, recommendation: ArchitectureRecommendation) -> str:
        """Save CloudFormation YAML template and return URL."""
        if not recommendation.iac_template:
            raise ValueError("recommendation.iac_template is empty")

        file_path = self._get_path(recommendation, ext="yaml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(recommendation.iac_template)

        return self._url(recommendation, ext="yaml")

    def _get_path(self, recommendation: ArchitectureRecommendation, *, ext: str) -> Path:
        return self.storage_path / f"{recommendation.recommendation_id}.{ext}"

    def _url(self, recommendation: ArchitectureRecommendation, *, ext: str) -> str:
        return f"{self.base_url}/{recommendation.recommendation_id}.{ext}"

