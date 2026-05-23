---
status: accepted
date: 2026-05-23
decision-makers: [fred]
---

# Use httpx as the HTTP Client

## Context and Problem Statement

hitchhikers needs an HTTP client to call the neolicense.ai REST API. The client must be lightweight (low install footprint for customers), support both sync and async usage patterns, and provide sensible defaults for a distributed SDK.

## Decision Drivers

- Customers may want async usage without adding a second HTTP library
- `requests` has no default timeout — hanging forever is unacceptable in a client SDK
- Single runtime dependency preferred
- Type annotations matter for a reference SDK

## Considered Options

1. `httpx` — modern sync+async HTTP client, built-in timeout defaults, typed
2. `requests` — ubiquitous, sync-only, no default timeout
3. `aiohttp` — async-only, would require `requests` alongside for sync use

## Decision Outcome

Chosen option: `httpx`, because it covers sync and async with one library, ships with sensible timeout defaults (overridden to 30s in `KiwiClient.__init__`), and is already a transitive dependency for customers using the Anthropic SDK or FastAPI. The Anthropic SDK and Stripe's Python SDK use the same approach.

### Consequences

- Good: One dep covers sync and async
- Good: Default timeout prevents silent hangs
- Good: Likely already installed in customer environments
- Bad: Not as universally pre-installed as `requests` for greenfield customers
- Bad: Still on `0.x` versioning (stable in practice, conservative on 1.0)

### Cost of Ownership

- **Maintenance burden**: Monitor httpx releases for breaking changes; version is pinned
- **Ongoing benefits**: If customers request async support, no new dep required
- **Sunset criteria**: Revisit if httpx API becomes unstable or `requests` gains async support

### Confirmation

`KiwiClient` instantiates `httpx.Client` with `timeout=30.0`. All 4 tests pass via `respx` mock without hitting real network.
