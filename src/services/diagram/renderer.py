"""Diagram rendering service with SVG/PNG rendering from Mermaid source."""

import base64
from typing import Optional
from pathlib import Path
import subprocess
import tempfile
import os


class DiagramRenderer:
    """Renders Mermaid diagrams to SVG/PNG formats."""

    def __init__(self, mermaid_cli_path: Optional[str] = None):
        """Initialize diagram renderer.

        Args:
            mermaid_cli_path: Path to Mermaid CLI (defaults to 'mmdc' in PATH)
        """
        self.mermaid_cli_path = mermaid_cli_path or "mmdc"

    def render_svg(
        self,
        mermaid_source: str,
        output_path: Optional[str] = None,
    ) -> str:
        """Render Mermaid diagram to SVG.

        Args:
            mermaid_source: Mermaid diagram source code
            output_path: Optional output file path

        Returns:
            SVG content as string
        """
        return self._render(mermaid_source, "svg", output_path)

    def render_png(
        self,
        mermaid_source: str,
        output_path: Optional[str] = None,
    ) -> bytes:
        """Render Mermaid diagram to PNG.

        Args:
            mermaid_source: Mermaid diagram source code
            output_path: Optional output file path

        Returns:
            PNG content as bytes
        """
        return self._render(mermaid_source, "png", output_path)

    def render_base64(
        self,
        mermaid_source: str,
        format: str = "svg",
    ) -> str:
        """Render Mermaid diagram to base64-encoded string.

        Args:
            mermaid_source: Mermaid diagram source code
            format: Output format ('svg' or 'png')

        Returns:
            Base64-encoded diagram content
        """
        if format == "svg":
            svg_content = self.render_svg(mermaid_source)
            return base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        elif format == "png":
            png_content = self.render_png(mermaid_source)
            return base64.b64encode(png_content).decode("utf-8")
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _render(
        self,
        mermaid_source: str,
        format: str,
        output_path: Optional[str] = None,
    ):
        """Render Mermaid diagram using Mermaid CLI.

        Args:
            mermaid_source: Mermaid diagram source code
            format: Output format ('svg' or 'png')
            output_path: Optional output file path

        Returns:
            Rendered diagram content
        """
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd", delete=False) as input_file:
            input_file.write(mermaid_source)
            input_file_path = input_file.name

        try:
            # Create temporary output file if not provided
            if output_path is None:
                output_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
                output_path = output_file.name
                output_file.close()

            # Run Mermaid CLI
            cmd = [
                self.mermaid_cli_path,
                "-i", input_file_path,
                "-o", output_path,
                "-f", format,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                # Fallback: return Mermaid source as-is if CLI not available
                if format == "svg":
                    return self._fallback_svg(mermaid_source)
                else:
                    raise RuntimeError(f"Mermaid CLI failed: {result.stderr}")

            # Read rendered output
            with open(output_path, "rb" if format == "png" else "r", encoding="utf-8" if format == "svg" else None) as f:
                content = f.read()

            # Clean up output file if we created it
            if output_path != output_path:
                os.unlink(output_path)

            return content

        finally:
            # Clean up input file
            if os.path.exists(input_file_path):
                os.unlink(input_file_path)

    def _fallback_svg(self, mermaid_source: str) -> str:
        """Generate fallback SVG when Mermaid CLI is not available.

        Args:
            mermaid_source: Mermaid diagram source code

        Returns:
            Simple SVG representation
        """
        # Encode Mermaid source for embedding
        encoded = base64.b64encode(mermaid_source.encode("utf-8")).decode("utf-8")
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
  <rect width="800" height="600" fill="white"/>
  <text x="400" y="300" text-anchor="middle" font-family="monospace" font-size="14">
    Mermaid Diagram (CLI not available)
  </text>
  <foreignObject x="50" y="50" width="700" height="500">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <pre style="font-family: monospace; font-size: 12px;">{mermaid_source}</pre>
    </div>
  </foreignObject>
</svg>"""
        return svg

