---
id: document-sdk-architecture
status: complete
date: 2026-05-23
complexity: 2
decision-makers: [fred]
---

# Document SDK Architecture Decisions

## Why

Capturing the settled architectural decisions made during initial scaffolding of the hitchhikers SDK so future contributors understand the constraints and don't inadvertently reverse them.

## Decisions

| # | Title | File |
|---|-------|------|
| 0001 | src/ layout for distribution | decisions/0001-src-layout-for-distribution.md |
| 0002 | httpx over requests | decisions/0002-httpx-over-requests.md |
| 0003 | X-API-Key authentication | decisions/0003-x-api-key-authentication.md |
| 0004 | OpenAPI codegen for schemas | decisions/0004-openapi-codegen-for-schemas.md |
| 0005 | DocumentState mirrors bake | decisions/0005-documentstate-mirrors-bake.md |

## Prior Art

- PyPA packaging guide: src/ layout is the current recommendation for distributed packages
- Anthropic Python SDK: uses httpx + X-API-Key style auth + codegen patterns
- Stripe Python SDK: custom exception hierarchy, typed response models
- ninja_apikey (bake dep): X-API-Key header confirmed from bake source

## No Features

These are pure architectural decisions. No Gherkin scenarios needed — behavior is tested via the existing test suite.
