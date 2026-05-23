---
change-id: add-dais-document-endpoints
title: Add DAIS document API endpoints to KiwiClient
status: draft
complexity: 3
date: 2026-05-23
---

## Why

Developers installing the hitchhikers SDK need clear behavioral specs for the four core DAIS document operations. The code scaffolding exists but has no feature specs, two behaviors need tightening (optional title, typed list params), and transient network failures are unhandled.

## What

### Features (new)
- `features/documents/list_documents.feature` — list and filter via GET /api/v2/dais/documents with typed params
- `features/documents/get_document.feature` — retrieve state/details via GET /api/v2/dais/documents/{id}
- `features/documents/get_document_attributes.feature` — retrieve extraction payloads via GET /api/v2/dais/documents/{id}/attributes
- `features/documents/upload_document.feature` — create document via POST /api/v1/dais/document/; title optional (defaults to filename); external_id optional but recommended
- `features/documents/get_transform_output.feature` — retrieve client transform output via GET /api/v2/dais/documents/{id}/transform-output; returns `Any` (arbitrary client-defined schema)
- `features/client/client_configuration.feature` — configure api_key, base_url, and max_retries at construction time

### Decisions (new)
- `decisions/0006-tenacity-retries.md` — adopt tenacity for retry behaviour; 2 retries default, overridable via constructor

### Data (external API contract)
- `data.yml` — request/response contracts for all four endpoints

## Behavior changes vs current code

| Area | Current | New |
|------|---------|-----|
| `upload_document` | `title: str` required, `doc_type: str` required | `title: str \| None = None` (derives from filename); `doc_type: str \| None = None` (optional but recommended) |
| `list_documents` | `**params` untyped pass-through | Strict typed params: `limit`, `offset`, `doc_type`, `business_partner_id`, `internal_legal_entity_id`, `start_date_gte`, `end_date_lte`; unknown kwargs rejected |
| `get_transform_output` | Not implemented | New method; returns `Any` — caller is responsible for parsing against their schema |
| All methods | No retry | Tenacity retries on 5xx and network errors; 2 retries default, overridable |
| `KiwiClient.__init__` | `api_key, base_url, timeout` | Add `max_retries: int = 2` |

## Assumptions

- **doc_type optional**: `doctype_name` is optional in the v1 upload form; server accepts omission.
- **Duplicate = error**: Bake raises an error (not returns existing ID) when a duplicate document is submitted. Upload POST is therefore **not safe to retry without external_id** — a successful-but-lost-in-transit upload will error on retry with a duplicate error rather than succeeding idempotently.
- **No env var fallback**: Constructor params are sufficient for installer ergonomics. No `KIWI_API_KEY` / `KIWI_BASE_URL` env var discovery added.
- **Backoff strategy**: Exponential backoff with tenacity defaults. Exact delays deferred to plan stage.

## Pre-Mortem

- **Upload retry creates duplicate error**: POST succeeds on server, response lost in transit, retry hits duplicate error. Callers without `external_id` get an unexpected APIError on retry. Mitigation: exclude upload from retry scope, or only retry if `external_id` is set; document clearly in SDK.
- **Tenacity major version break**: Retry logic silently breaks if tenacity API changes. Mitigation: pin `tenacity>=8,<9` in pyproject.toml.
- **Filter param drift**: Swagger-sourced filter list may diverge from live API. Mitigation: contract tests against staging as part of CI.
- **Strict typed params is a breaking change**: Callers using `list_documents(custom_param="x")` today will get a TypeError. Mitigation: treat as intentional — document in changelog as breaking.

## Prior Art

All four HTTP methods are scaffolded in `src/hitchhikers/client.py`. Schemas are generated from OpenAPI in `src/hitchhikers/schemas/`. This change adds behavioral specs, tightens two method signatures, and adds a retry dependency. No third-party document management SDK evaluated — the API is proprietary (Kiwi DAIS). Retry library selection in ADR 0006; complements existing ADR 0002 (httpx over requests).
