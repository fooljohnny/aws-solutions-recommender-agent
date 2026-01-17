# Solution KB Diagram Collection Plan (1000 items)

## Goal
Collect at least 1000 mature, production-grade solution architecture diagrams backed by
CloudFormation or Terraform templates, and store them in the repository for knowledge
graph (KG) construction and retrieval.

## Scope
- Inputs: CloudFormation (YAML/JSON) and Terraform module sources.
- Outputs: Template assets, diagram assets, and a manifest that links templates to diagrams.
- Storage: `data/solution_kb/` with a normalized manifest for KG ingestion.

## Preferred channels (priority order)
1. AWS Partner Solutions / QuickStart (`aws_quickstart`)
2. AWS Solutions Library (`aws_solutions`)
3. AWS Serverless Application Repository (`aws_sar`)
4. AWS-IA (`aws_ia`)
5. Terraform AWS Modules (`terraform_aws_modules`)
6. AWS Samples (`aws_samples`)
7. Commercial / Community (`community`)

These map to `TemplateSource` values used in the KB store and ranking logic.

## Data layout
```
data/solution_kb/
  sources/        # local clones or mirrored source packages
  templates/      # normalized template copies (optional but recommended)
  diagrams/       # collected or generated diagram files
  manifests/
    template_manifest.jsonl
  targets.yaml
  sources.yaml
```

## Manifest fields (template_manifest.jsonl)
Each line is a JSON object describing one template and its diagram:
- `template_id`
- `template_name`
- `template_kind`
- `source`
- `repository`
- `template_path`
- `diagram_path`
- `diagram_format`
- `diagram_mode` (repo | auto | missing)
- `diagram_source_path` (optional)
- `resource_types`
- `tags`, `industries`, `business_types`
- `collected_at`

## Collection workflow
1. Clone or mirror target sources under `data/solution_kb/sources/`.
2. Create `data/solution_kb/sources.yaml` (see `sources.example.yaml`).
3. Run `scripts/solution_kb/collect.py` to:
   - ingest templates into the KB store
   - copy templates into `data/solution_kb/templates/` (optional)
   - collect repo-provided diagrams or generate Mermaid-based diagrams
   - build or update `template_manifest.jsonl`
4. Run `scripts/solution_kb/audit.py` to validate counts and coverage.

## Diagram strategy
- Prefer repo-provided SVG/PNG when found near templates.
- If missing, generate Mermaid from resource topology and store as `.mmd` or `.svg`.
- Track diagram origin in `diagram_mode`.

## Targets (initial distribution)
Targets are stored in `data/solution_kb/targets.yaml` and tracked via the audit script:
- aws_quickstart: 250
- aws_solutions: 120
- aws_sar: 200
- aws_ia: 150
- terraform_aws_modules: 180
- aws_samples: 70
- community: 30

## Quality gates
- Each template must have a valid `source` and `repository`.
- Each template should include `name` or `description` plus at least one tag.
- Each manifest entry must resolve to a local diagram path.
- Duplicate templates are removed by `template_id` and content hash.

## Phased execution
1. Phase A (core sources): QuickStart, Solutions, SAR (target ~570)
2. Phase B (coverage): AWS-IA, Terraform Modules (target ~330)
3. Phase C (backfill): Samples + Community (target ~100)
4. Phase D (QA + backfill): audit, resolve missing diagrams, finalize 1000+
