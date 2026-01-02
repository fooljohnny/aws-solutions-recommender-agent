"""Diagram generation service with Mermaid diagram generation from architecture data."""

from typing import List, Dict, Any
from ...models.architecture_recommendation import ArchitectureRecommendation
from ...models.service import Service
from .icons import AWSIconMapper


class DiagramGenerator:
    """Generates Mermaid diagrams from architecture recommendations."""

    def __init__(self):
        """Initialize diagram generator."""
        self.icon_mapper = AWSIconMapper()

    def generate_mermaid(
        self,
        recommendation: ArchitectureRecommendation,
        diagram_type: str = "graph",
    ) -> str:
        """Generate Mermaid diagram source code from architecture recommendation.

        Args:
            recommendation: Architecture recommendation
            diagram_type: Diagram type ('graph', 'flowchart', 'sequence')

        Returns:
            Mermaid diagram source code
        """
        if diagram_type == "graph" or diagram_type == "flowchart":
            return self._generate_flowchart(recommendation)
        elif diagram_type == "sequence":
            return self._generate_sequence_diagram(recommendation)
        else:
            return self._generate_flowchart(recommendation)

    def _generate_flowchart(self, recommendation: ArchitectureRecommendation) -> str:
        """Generate flowchart diagram.

        Args:
            recommendation: Architecture recommendation

        Returns:
            Mermaid flowchart source code
        """
        services = recommendation.services
        if not services:
            return "graph TB\n    A[No Services]\n"

        # Build node definitions
        nodes = []
        edges = []

        for service in services:
            node_id = self._sanitize_id(service.service_id)
            label = f"{service.aws_service_name}\\n{service.role}"
            nodes.append(f"    {node_id}[\"{label}\"]")

            # Add edges for dependencies
            for dep_id in service.dependencies:
                dep_service = next(
                    (s for s in services if s.service_id == dep_id),
                    None,
                )
                if dep_service:
                    dep_node_id = self._sanitize_id(dep_service.service_id)
                    edges.append(f"    {dep_node_id} --> {node_id}")

        # If no explicit dependencies, create logical flow
        if not edges and len(services) > 1:
            # Simple sequential flow
            for i in range(len(services) - 1):
                node_id_1 = self._sanitize_id(services[i].service_id)
                node_id_2 = self._sanitize_id(services[i + 1].service_id)
                edges.append(f"    {node_id_1} --> {node_id_2}")

        diagram = "graph TB\n"
        diagram += "\n".join(nodes)
        if edges:
            diagram += "\n"
            diagram += "\n".join(edges)

        return diagram

    def _generate_sequence_diagram(
        self,
        recommendation: ArchitectureRecommendation,
    ) -> str:
        """Generate sequence diagram.

        Args:
            recommendation: Architecture recommendation

        Returns:
            Mermaid sequence diagram source code
        """
        services = recommendation.services
        if not services:
            return "sequenceDiagram\n    participant User\n    User->>System: No Services\n"

        diagram = "sequenceDiagram\n"
        diagram += "    participant User\n"

        for service in services:
            diagram += f"    participant {service.aws_service_name}\n"

        # Simple interaction flow
        if services:
            diagram += f"    User->>{services[0].aws_service_name}: Request\n"
            for i in range(len(services) - 1):
                diagram += f"    {services[i].aws_service_name}->>{services[i + 1].aws_service_name}: Process\n"
            diagram += f"    {services[-1].aws_service_name}-->>User: Response\n"

        return diagram

    def _sanitize_id(self, service_id) -> str:
        """Sanitize service ID for use in Mermaid diagram.

        Args:
            service_id: Service UUID

        Returns:
            Sanitized ID string
        """
        # Use first 8 characters of UUID
        return f"S{str(service_id).replace('-', '')[:8]}"

