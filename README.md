# hitchhikers 🐦

<p align="center">
  <img src="assets/logo.png" alt="hitchhikers logo" width="300" />
</p>

Don't panic. This is the guide.

The Kiwi Data Python reference implementation — a working example of how to integrate with the Kiwi Data document processing API.

[![PyPI](https://img.shields.io/pypi/v/hitchhikers)](https://pypi.org/project/hitchhikers/) [![CI](https://github.com/KiwiData-AI/hitchhikers/actions/workflows/ci.yml/badge.svg)](https://github.com/KiwiData-AI/hitchhikers/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What Kiwi Data does

Kiwi Data extracts structured data from unstructured documents. Contracts, purchase orders, leases, financial statements — the kind of PDFs that live in shared drives and quietly cause compliance problems.

AI extracts the fields. Validation layers check the AI's work. Human reviewers confirm what the machines aren't sure about.

"Looks right" and "is right" are different things, especially in procurement and compliance.

---

## What this repo shows

- How to authenticate and initialize the client
- How to upload a document and link it to your own system's record ID
- How to poll document state through the processing pipeline
- How to retrieve extracted attributes and transform outputs
- How to handle retries, timeouts, and API errors correctly
- How to write typed, validated API interactions with Pydantic schemas

---

## Prerequisites

- Python 3.11+
- A Kiwi Data API key — contact [fred@kiwidata.com](mailto:fred@kiwidata.com) to get one
- `uv` or `pip` for package management

---

## Quickstart

**1. Install**

```bash
pip install hitchhikers
```

Or with uv:

```bash
uv add hitchhikers
```

**2. Initialize the client**

```python
from hitchhikers import KiwiClient

client = KiwiClient(api_key="your-api-key")
```

**3. Upload a document**

```python
doc = client.upload_document(
    file_path="contract.pdf",
    doc_type="contract",
    external_id="CRM-12345",  # your internal record ID — recommended for idempotency
)
print(doc.document_id)
```

**4. Poll until processing is complete**

```python
from hitchhikers import DocumentState
import time

while True:
    detail = client.get_document(doc.document_id)
    state = DocumentState(detail.docstate_name)
    if state.is_done:
        break
    if state.is_error:
        raise RuntimeError(f"Processing failed: {state}")
    time.sleep(5)
```

**5. Retrieve extracted attributes**

```python
attributes = client.get_document_attributes(doc.document_id)
for attr in attributes:
    print(attr)
```

**6. Retrieve transform output**

Transform output shape varies by document type and your configured transform. Parse it against your own schema.

```python
output = client.get_transform_output(doc.document_id)
```

---

## Best practices

**Use the context manager.** It closes the underlying HTTP connection cleanly.

```python
with KiwiClient(api_key="your-api-key") as client:
    doc = client.upload_document("invoice.pdf", doc_type="invoice")
```

**Always set `external_id`.** It ties the document back to your system's record 

**Handle errors explicitly.** The client raises typed exceptions — catch what you care about.

```python
from hitchhikers import AuthenticationError, NotFoundError, APIError

try:
    detail = client.get_document(document_id)
except NotFoundError:
    # document doesn't exist
    ...
except AuthenticationError:
    # bad or expired API key
    ...
except APIError as e:
    # unexpected 4xx or 5xx
    print(e.status_code, e)
```

**Retries are on by default.** `KiwiClient` retries on 5xx errors and network failures with exponential backoff (2 attempts by default). Set `max_retries=0` to disable.

**Attributes are empty until processing completes.** `get_document_attributes` returns an empty list while the document is still in `NEW`, `EXTRACTED`, or `TRANSFORMED` state. Always check `DocumentState.is_done` first.

---

## How it works

`KiwiClient` wraps the Kiwi Data REST API with typed request/response models via Pydantic and automatic retry logic via Tenacity. Documents move through a state machine: `NEW` → `EXTRACTED` → `TRANSFORMED` → `PUBLISHED`, with `HUMAN_REVIEW` as a gate before final publish when the AI's confidence is low. Extraction attributes and transform outputs are available once the document clears its processing stage.

---

## Project structure

```
hitchhikers/
├── src/hitchhikers/
│   ├── client.py          # KiwiClient — all API methods live here
│   ├── enums.py           # DocumentState with is_done / is_error helpers
│   ├── exceptions.py      # APIError, AuthenticationError, NotFoundError
│   └── schemas/
│       ├── v1.py          # Upload and document schemas (codegen from OpenAPI)
│       └── v2.py          # Detail, list, and attribute schemas (codegen from OpenAPI)
├── tests/                 # Unit tests, mocked with respx
├── features/              # BDD feature specs (Gherkin)
└── pyproject.toml
```

---

## Contributing

This is a reference implementation. PRs that fix real issues are welcome. Feature requests belong in a conversation with the Kiwi Data team.

**Setup:**

```bash
uv sync --extra dev
```

**Run tests:**

```bash
pytest
```

**Lint and type-check:**

```bash
black src tests
flake8 src tests
pyright src
```

**Commit conventions.** Use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | When |
|--------|------|
| `feat:` | New capability |
| `fix:` | Bug fix |
| `chore:` | Tooling, deps, CI |
| `docs:` | README, docstrings only |
| `refactor:` | No behavior change |
| `test:` | Tests only |

Keep commits atomic — one logical change per commit. Don't bundle unrelated fixes.

**Branch naming:** `feat/short-description`, `fix/short-description`.

**Changelog is automatic.** Commit messages feed [git-cliff](https://git-cliff.org) — `CHANGELOG.md` updates itself on every release. Write good commit messages; the changelog writes itself.

See [CHANGELOG.md](CHANGELOG.md) for release history.

---

## License

[MIT](LICENSE). So long, and thanks for all the fish.
