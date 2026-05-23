---
status: accepted
date: 2026-05-23
decision-makers: [fred]
---

# Authenticate with X-API-Key Header

## Context and Problem Statement

The neolicense.ai API (`bake`) supports two authentication schemes: JWT Bearer tokens (for browser/session users) and API keys via `ninja_apikey` (for system-to-system integrations). hitchhikers targets system-to-system use — customers integrating from their own backend systems.

## Decision Drivers

- SDK targets automated/backend use, not browser sessions
- JWT Bearer tokens require a login flow and token refresh — inappropriate for a server-side SDK
- `bake` uses `ninja_apikey` which expects the `X-API-Key` header on all v2 routes
- Key format from `ninja_apikey` is `{prefix}.{key}` (e.g. `abc12.secretvalue`)

## Considered Options

1. `X-API-Key` header with `ninja_apikey` keys
2. `Authorization: Bearer {token}` with JWT

## Decision Outcome

Chosen option: `X-API-Key`, because it is the correct header for `ninja_apikey` (confirmed in `bake` source: `HTTP_X_API_KEY` in test client = `X-API-Key` in HTTP). Bearer tokens are for session-based UI access and require refresh logic unsuitable for an SDK.

### Consequences

- Good: Stateless — no token refresh needed
- Good: Matches `bake`'s `ninja_apikey` implementation exactly
- Bad: API keys are long-lived — customers must rotate them if compromised

### Cost of Ownership

- **Maintenance burden**: If `bake` adds OAuth2 or changes auth middleware, SDK must be updated
- **Ongoing benefits**: Simple — one header, no refresh flow
- **Sunset criteria**: Revisit if neolicense.ai adds OAuth2 client credentials flow

### Confirmation

Verified against `bake` source: `dais/api.py` routes use `auth=[ClientAuth(), APIKeyAuth()]`. `APIKeyAuth` from `ninja_apikey.security` reads the `X-API-Key` header. Test steps confirm with `HTTP_X_API_KEY=context.ricky_api_key`.
