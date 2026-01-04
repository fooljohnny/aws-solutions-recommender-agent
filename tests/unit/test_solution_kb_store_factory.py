from __future__ import annotations

import os

from src.services.solution_kb.store_factory import get_solution_kb_store


def test_store_factory_defaults_to_file_store_when_no_neo4j(monkeypatch):
    monkeypatch.delenv("SOLUTION_KB_BACKEND", raising=False)
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)

    store = get_solution_kb_store(root_dir=".solution_kb_test")
    # File store class lives in solution_kb.store as SolutionKBStore
    assert store.__class__.__name__ == "SolutionKBStore"

