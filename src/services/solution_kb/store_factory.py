"""KB store factory.

Default behavior:
- If SOLUTION_KB_BACKEND=neo4j OR NEO4J_URI is set -> use Neo4j graph store.
- Otherwise -> use local file store (.solution_kb/templates.jsonl).
"""

from __future__ import annotations

import os
from typing import Optional

from .store import SolutionKBStore


def get_solution_kb_store(*, root_dir: Optional[str] = None) -> SolutionKBStore:
    backend = (os.getenv("SOLUTION_KB_BACKEND") or "").strip().lower()
    neo4j_uri = (os.getenv("NEO4J_URI") or "").strip()

    if backend == "neo4j" or (backend == "" and neo4j_uri):
        # Lazy import so local-only installs don't require Neo4j deps at import time.
        from .neo4j_store import Neo4jSolutionKBStore

        return Neo4jSolutionKBStore.from_env()

    return SolutionKBStore(root_dir=root_dir)

