# Solution KB data directory

This directory stores the assets used to build the solution template knowledge base.
It is designed to keep templates, diagrams, and manifests in a predictable layout so
the KB pipeline can ingest and validate assets locally.

## Layout
```
data/solution_kb/
  sources/        # local clones or mirrored source packages
  templates/      # normalized template copies (optional but recommended)
  diagrams/       # collected or generated diagram files
  manifests/      # JSONL manifests linking templates to diagrams
  targets.yaml    # quota targets by source
  sources.yaml    # collection config (see sources.example.yaml)
```

## Files
- `sources.example.yaml`: template config for collection runs.
- `targets.yaml`: quota targets (used by audit script).
- `manifests/template_manifest.jsonl`: one JSON object per template.

## Suggested usage
1. Place your cloned repos under `sources/`.
2. Copy `sources.example.yaml` to `sources.yaml` and update paths.
3. Run `python scripts/solution_kb/collect.py --config data/solution_kb/sources.yaml`.
4. Run `python scripts/solution_kb/audit.py --manifest data/solution_kb/manifests/template_manifest.jsonl`.
