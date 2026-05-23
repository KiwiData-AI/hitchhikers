---
status: proposed
date: 2026-05-23
---

# 0006 — Tenacity for Retry Behaviour

## Status
Proposed

## Context
The DAIS API is a remote HTTP service subject to transient failures: network blips, brief server overload, 503s during deploys. Without retry logic, callers see immediate failures for recoverable situations, requiring them to implement retries themselves — inconsistently, if at all.

## Decision
Use **tenacity** for retry behaviour wrapping `KiwiClient._request()`.

- Default: 2 retries (3 total attempts) with exponential backoff
- Retryable conditions: HTTP 5xx responses, `httpx.TimeoutException`, `httpx.ConnectError`
- Not retried: 4xx responses — these are client errors (auth, not-found, bad input) where retrying cannot succeed
- `max_retries` constructor param overrides the default; `max_retries=0` disables retries entirely

## Considered Options

| Option | Notes |
|--------|-------|
| **tenacity** | Library-agnostic, composable decorators, battle-tested, handles both exception and return-value retry conditions |
| **httpx built-in** | httpx has no retry mechanism in its sync client |
| **urllib3 Retry + transport** | Possible via `httpx.HTTPTransport(retries=...)` but only retries connection errors, not 5xx response codes |
| **Manual loop in _request** | Avoids a dependency but reimplements backoff/jitter logic that tenacity provides correctly |

Tenacity wins: it handles both HTTP status retries and network-level retries cleanly, and is already widely used in Python service clients.

## Consequences

- Adds `tenacity` as a dependency (pure Python, no C extensions)
- Latency increases on retried requests by design
- POST /upload_document retry safety: bake rejects duplicate submissions with an error. A successful-but-lost-in-transit upload would therefore error on retry rather than succeed idempotently. Upload POST should be excluded from retry scope or only retried when `external_id` is present — decision deferred to plan stage.
- Pin to `tenacity>=8,<9` to prevent silent breakage from future major versions
