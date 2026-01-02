"""Diagram storage and URL generation with file storage and download link generation."""

import os
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime
from ...models.architecture_recommendation import ArchitectureRecommendation
from .renderer import DiagramRenderer


class DiagramStorage:
    """Manages diagram storage and URL generation."""

    def __init__(
        self,
        storage_path: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize diagram storage.

        Args:
            storage_path: Base path for storing diagrams (defaults to ./diagrams)
            base_url: Base URL for diagram access (defaults to /diagrams)
        """
        self.storage_path = Path(storage_path or "./diagrams")
        self.base_url = base_url or "/diagrams"
        self.renderer = DiagramRenderer()

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_diagram(
        self,
        recommendation: ArchitectureRecommendation,
        format: str = "svg",
    ) -> str:
        """Save diagram for recommendation and return URL.

        Args:
            recommendation: Architecture recommendation
            format: Diagram format ('svg', 'png', or 'mermaid')

        Returns:
            Diagram URL
        """
        if format == "mermaid":
            # Save Mermaid source directly
            diagram_content = recommendation.diagram_data
            file_path = self._get_diagram_path(recommendation, "mmd")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(diagram_content)
        else:
            # Render and save
            if format == "svg":
                diagram_content = self.renderer.render_svg(recommendation.diagram_data)
                file_path = self._get_diagram_path(recommendation, "svg")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(diagram_content)
            elif format == "png":
                diagram_content = self.renderer.render_png(recommendation.diagram_data)
                file_path = self._get_diagram_path(recommendation, "png")
                with open(file_path, "wb") as f:
                    f.write(diagram_content)
            else:
                raise ValueError(f"Unsupported format: {format}")

        # Generate and return URL
        url = self._generate_url(recommendation, format)
        return url

    def get_diagram_url(
        self,
        recommendation: ArchitectureRecommendation,
        format: str = "svg",
    ) -> str:
        """Get diagram URL for recommendation.

        Args:
            recommendation: Architecture recommendation
            format: Diagram format

        Returns:
            Diagram URL
        """
        return self._generate_url(recommendation, format)

    def _get_diagram_path(
        self,
        recommendation: ArchitectureRecommendation,
        extension: str,
    ) -> Path:
        """Get file path for diagram.

        Args:
            recommendation: Architecture recommendation
            extension: File extension

        Returns:
            File path
        """
        # Use recommendation ID for filename
        filename = f"{recommendation.recommendation_id}.{extension}"
        return self.storage_path / filename

    def _generate_url(
        self,
        recommendation: ArchitectureRecommendation,
        format: str,
    ) -> str:
        """Generate URL for diagram.

        Args:
            recommendation: Architecture recommendation
            format: Diagram format

        Returns:
            Diagram URL
        """
        filename = f"{recommendation.recommendation_id}.{format}"
        return f"{self.base_url}/{filename}"

    def delete_diagram(
        self,
        recommendation_id: str,
        format: str = "svg",
    ) -> bool:
        """Delete diagram file.

        Args:
            recommendation_id: Recommendation ID
            format: Diagram format

        Returns:
            True if deleted successfully
        """
        extension = format if format != "mermaid" else "mmd"
        file_path = self.storage_path / f"{recommendation_id}.{extension}"
        if file_path.exists():
            file_path.unlink()
            return True
        return False

