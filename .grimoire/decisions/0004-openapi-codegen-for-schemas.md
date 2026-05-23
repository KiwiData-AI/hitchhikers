---
status: accepted
date: 2026-05-23
decision-makers: [fred]
---

# Generate Response Schemas from bake's OpenAPI Spec

## Context and Problem Statement

hitchhikers needs typed response models for the neolicense.ai API. Maintaining hand-written schemas in parallel with `bake`'s evolving API creates drift and duplication. The source of truth must be `bake`.

## Decision Drivers

- Avoid duplicating schema definitions across repos
- Customers benefit from typed responses (IDE completion, validation)
- Schema drift between SDK and API is a support burden
- `pydantic` models match what Django Ninja already generates

## Considered Options

1. Generate from `bake`'s OpenAPI JSON using `datamodel-codegen`
2. Hand-write pydantic models in hitchhikers
3. Install `bake` as a dev dep and import schemas directly (pulls Django + all of bake)

## Decision Outcome

Chosen option: codegen from OpenAPI, because it derives types directly from the API contract, requires no manual maintenance for covered endpoints, and ships only pydantic models (not Django). `scripts/filter_openapi.py` trims the spec to only the paths hitchhikers cares about before codegen, keeping generated files minimal.

### Adding a New Endpoint — Workflow

1. Add the path string to `scripts/generate_models.sh` filter args
2. Run `bash scripts/generate_models.sh` (requires live bake at `$BAKE_URL`)
3. Import new model(s) from `schemas/v1.py` or `schemas/v2.py` into `client.py`
4. Add the method to `KiwiClient`
5. Add a `respx`-mocked test in `tests/`

**Never hand-edit `schemas/v1.py` or `schemas/v2.py`.** They are outputs. Edits are wiped on next regeneration. If a schema is wrong, fix it in `bake` or adjust the filter.

### Generated Files

| File | Source spec | Regenerate with |
|------|-------------|-----------------|
| `src/hitchhikers/schemas/v1.py` | `GET /api/v1/openapi.json` | `bash scripts/generate_models.sh` |
| `src/hitchhikers/schemas/v2.py` | `GET /api/openapi.json` | `bash scripts/generate_models.sh` |

### Consequences

- Good: Schema drift is a script run away from being fixed
- Good: Customers get pydantic v2 models with full validation
- Bad: Regeneration requires a running `bake` instance
- Bad: Generated files are verbose (domain enums pulled in transitively)

### Cost of Ownership

- **Maintenance burden**: Run `generate_models.sh` when covered API endpoints change; commit updated schemas
- **Ongoing benefits**: Zero manual schema maintenance for covered endpoints
- **Sunset criteria**: If bake stops exposing OpenAPI, or if schema volume becomes unmanageable

### Confirmation

`bash scripts/generate_models.sh` produces valid Python from live bake. `KiwiClient` methods return validated pydantic model instances. Test suite passes.
