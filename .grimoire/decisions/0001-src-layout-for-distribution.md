---
status: accepted
date: 2026-05-23
decision-makers: [fred]
---

# Use src/ Layout for Packaged Distribution

## Context and Problem Statement

hitchhikers is a pip-installable SDK. The package structure must prevent the source tree from being accidentally imported during testing (where tests would run against raw source rather than the installed package), and must be correctly discoverable by build tools.

## Decision Drivers

- Customers install via `pip install hitchhikers` — packaging must be correct
- Tests must run against the installed package, not the source tree
- Standard tooling (uv, setuptools, pyright) must locate the package without config hacks

## Considered Options

1. `src/` layout — package lives under `src/hitchhikers/`
2. Flat layout — package lives at root `hitchhikers/`

## Decision Outcome

Chosen option: `src/` layout, because it physically separates source from the project root, preventing accidental `import hitchhikers` from resolving to the source tree during test runs. This is the packaging standard recommended by PyPA for distributed packages.

### Consequences

- Good: Tests always run against the installed package
- Good: `pyproject.toml` with `[tool.setuptools.packages.find] where = ["src"]` is all that's needed
- Bad: Slightly unfamiliar to contributors used to flat layout

### Cost of Ownership

- **Maintenance burden**: None — one-time layout choice with no ongoing cost
- **Ongoing benefits**: Correct test isolation by default; pyright resolves the package correctly via `pyrightconfig.json`
- **Sunset criteria**: Revisit if the packaging ecosystem standardises on flat layout

### Confirmation

`pytest` resolves `from hitchhikers import KiwiClient` against the installed package. Confirmed by clean `uv pip install -e ".[dev]"` + passing test suite.
