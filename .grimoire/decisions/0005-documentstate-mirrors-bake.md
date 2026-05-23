---
status: accepted
date: 2026-05-23
decision-makers: [fred]
---

# DocumentState Enum Must Mirror bake's DocumentStates Exactly

## Context and Problem Statement

`bake` manages document lifecycle via a Django FSM on `Document.state`. hitchhikers exposes `DocumentState` so customers can branch on state values without using raw strings. If these diverge, customer code silently breaks.

## Decision Drivers

- Raw string comparison is error-prone for customers
- State values come from `bake`'s `DocumentStates` enum (`doc_types/enums.py`)
- Adding convenience properties (`is_done`, `is_in_progress`, `is_error`) requires knowing which states mean what

## Considered Options

1. Mirror `bake`'s `DocumentStates` exactly in `enums.py`
2. Expose only a subset of states relevant to the alpha use case
3. Return raw strings and let customers compare themselves

## Decision Outcome

Chosen option: full mirror, because partial exposure causes confusion when customers observe states not in the SDK enum, and raw strings remove IDE support. The full state set is small (11 values) and stable.

### State Semantics

| State | Category |
|-------|----------|
| `NEW`, `EXTRACTED`, `TRANSFORMED` | In progress |
| `LOCKED`, `PUBLISHED` | Done |
| `HUMAN_REVIEW`, `EXTRACT_ERROR`, `TRANSFORM_ERROR`, `PUBLISH_ERROR`, `ERROR` | Needs attention |
| `DELETED` | Gone |

**Done = LOCKED or PUBLISHED only.** `EXTRACTED` and `TRANSFORMED` are intermediate pipeline states, not complete.

### Maintenance Rule

When `bake`'s `DocumentStates` enum changes, update `src/hitchhikers/enums.py` to match before releasing a new SDK version. Check `bake/doc_types/enums.py:DocumentStates` as the source of truth.

### Consequences

- Good: Customers get IDE completion and typo protection on state values
- Good: `is_done`, `is_in_progress`, `is_error` properties encode business semantics clearly
- Bad: bake state additions are a breaking omission until SDK is updated

### Cost of Ownership

- **Maintenance burden**: Manual sync required when bake adds/renames states
- **Ongoing benefits**: Type-safe state handling for all customers
- **Sunset criteria**: If bake exposes states via API schema, generate this enum too

### Confirmation

`DocumentState` values confirmed against `bake/doc_types/enums.py:DocumentStates` on 2026-05-23. `StrEnum` used so `doc.state == DocumentState.LOCKED` works against raw API strings.
