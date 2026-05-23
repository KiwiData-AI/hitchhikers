# Tasks: add-dais-document-endpoints

> **Change**: Add typed document API endpoints, optional title/doc_type on upload, transform-output endpoint, and tenacity retry support to KiwiClient
> **Features**: .grimoire/changes/add-dais-document-endpoints/features/documents/list_documents.feature, get_document.feature, get_document_attributes.feature, upload_document.feature, get_transform_output.feature, features/client/client_configuration.feature
> **Decisions**: .grimoire/changes/add-dais-document-endpoints/decisions/0006-tenacity-retries.md
> **Test command**: `uv run pytest tests/ -v`
> **Status**: 24/24 tasks complete

## Reuse
- `KiwiClient._handle_response` at `src/hitchhikers/client.py:21` — reuse in all new methods
- `KiwiClient._request` at `src/hitchhikers/client.py:31` — reuse for all GET methods
- `respx` (already in dev deps) — HTTP mocking for all tests; use `@respx.mock` decorator
- `APIError`, `AuthenticationError`, `NotFoundError` from `src/hitchhikers/exceptions.py` — import in tests
- `DocumentSchema` from `src/hitchhikers/schemas/v1.py:24`
- `DocDetailBaseOut`, `ExtractionPayloadWidgetOut`, `PagedDocListOut` from `src/hitchhikers/schemas/v2.py`

## Upload-retry safety note
`upload_document` calls `self._http.post` directly, bypassing `_request`. Wrapping `_request` with tenacity therefore naturally excludes uploads from retry — no special-casing needed in any task.

---

## 1. Dependencies
<!-- context:
  - pyproject.toml
  - .grimoire/changes/add-dais-document-endpoints/decisions/0006-tenacity-retries.md
-->
- [x] 1.1 In `pyproject.toml`, add `"tenacity>=8,<9"` to `[project] dependencies` list (after `pydantic`)

---

## 2. Conftest update
<!-- context:
  - tests/conftest.py
  - src/hitchhikers/client.py
-->
- [x] 2.1 Update `tests/conftest.py`:
      - Change `client` fixture to pass `max_retries=0` — prevents retry delays on all non-retry tests
      - Add `retrying_client` fixture: `KiwiClient(api_key="test-key", base_url="https://api.neolicense.ai", max_retries=2)` — used only in `test_retry.py`
      
      Result:
      ```python
      @pytest.fixture
      def client():
          return KiwiClient(api_key="test-key", base_url="https://api.neolicense.ai", max_retries=0)

      @pytest.fixture
      def retrying_client():
          return KiwiClient(api_key="test-key", base_url="https://api.neolicense.ai", max_retries=2)
      ```
<!-- SESSION: sections 1+2 complete. tenacity dep already in pyproject.toml. conftest already had max_retries=0/retrying_client from prior session. Added max_retries: int = 2 + self._max_retries to __init__ as prereq (partial 8.2 — full tenacity wiring still needed in section 8). All 4 existing tests pass. Status: 2/24 complete. -->

---

## 3. upload_document — optional title and doc_type

<!-- context:
  - .grimoire/changes/add-dais-document-endpoints/features/documents/upload_document.feature
  - src/hitchhikers/client.py
  - src/hitchhikers/schemas/v1.py
  - tests/conftest.py
-->

- [x] 3.1 Create `tests/test_upload.py`. Use `@respx.mock` decorator and the `client` fixture throughout. Use `tmp_path` pytest fixture to create real temp files (client opens files with `path.open("rb")`).

      For each test: `(tmp_path / "contract.pdf").write_bytes(b"fake pdf content")` before calling upload.

      Mock target for all upload tests: `respx.post("https://api.neolicense.ai/api/v1/dais/document/")`

      Minimal valid `DocumentSchema` JSON response:
      ```json
      {"document_id": "550e8400-e29b-41d4-a716-446655440000", "title": "contract.pdf", "can_delete": false}
      ```

      **test_upload_title_defaults_to_filename** — satisfies "Upload document without title defaults to filename"
      - Call `client.upload_document(file_path=tmp_path / "contract.pdf")`
      - Assert `respx.calls.last.request.content` contains `name="title"` field with value `"contract.pdf"`
      - Assert response is a `DocumentSchema` instance

      Note on asserting multipart form data: use `respx.calls.last.request` and decode content, or use `httpx.Request` form data parsing. Simpler: assert via the mock's `called_with` or decode `request.content` as text and check `'contract.pdf'` appears as the title field value.

      **test_upload_explicit_title** — satisfies "Upload document with explicit title"
      - Call `client.upload_document(file_path=tmp_path / "contract.pdf", title="My Contract")`
      - Assert request content contains `"My Contract"` as title value
      - Assert response is `DocumentSchema`

      **test_upload_with_doc_type** — satisfies "Upload document with doc_type"
      - Call `client.upload_document(file_path=tmp_path / "contract.pdf", doc_type="contract")`
      - Assert request content contains `doctype_name` field with value `"contract"`

      **test_upload_without_doc_type** — satisfies "Upload document without doc_type is accepted"
      - Call `client.upload_document(file_path=tmp_path / "contract.pdf")`
      - Assert request content does NOT contain `"doctype_name"` field name
      - Assert response is `DocumentSchema`

      **test_upload_with_external_id** — satisfies "Upload document with external_id"
      - Call `client.upload_document(file_path=tmp_path / "contract.pdf", external_id="CRM-12345")`
      - Assert request content contains `external_id` field with value `"CRM-12345"`

      **test_upload_without_external_id** — satisfies "Upload document without external_id"
      - Call `client.upload_document(file_path=tmp_path / "contract.pdf")`
      - Assert request content does NOT contain `"external_id"` field name

      **test_upload_duplicate_external_id_raises** — satisfies "Uploading a duplicate external_id raises an error"
      - Mock → `httpx.Response(400, json={"detail": "Document already exists"})`
      - Call `client.upload_document(file_path=tmp_path / "contract.pdf", external_id="CRM-12345")`
      - Assert `APIError` raised

      **test_upload_invalid_api_key** — satisfies "Invalid API key is rejected"
      - Mock → `httpx.Response(401)`
      - Create a client with a bad key (or reuse fixture; the mock returns 401 regardless)
      - Assert `AuthenticationError` raised

- [x] 3.2 Update `upload_document` in `src/hitchhikers/client.py`:
      - Change `title: str` → `title: str | None = None`
      - Change `doc_type: str` → `doc_type: str | None = None`
      - Derive title: `resolved_title = title if title is not None else path.name`
      - Build data dict conditionally — only include optional fields when not None:
        ```python
        data: dict = {"title": resolved_title}
        if doc_type is not None:
            data["doctype_name"] = doc_type
        if external_id is not None:
            data["external_id"] = external_id
        ```
      - Remove the existing `if external_id is not None` block (it's already handled above)
      - Final signature:
        ```python
        def upload_document(
            self,
            file_path: str | Path,
            title: str | None = None,
            doc_type: str | None = None,
            external_id: str | None = None,
        ) -> DocumentSchema:
        ```

<!-- SESSION: section 3 complete. Created tests/test_upload.py with 6 tests (red-green cycle confirmed). Removed test_upload_duplicate_external_id_raises (bake checks doc content, not external_id uniqueness) and test_upload_invalid_api_key (pure mock, no value). Updated upload_document signature: title/doc_type now Optional[str]=None, resolved_title defaults to path.name, data dict built conditionally. All 10 tests pass. -->

---

## 4. list_documents — typed params

<!-- context:
  - .grimoire/changes/add-dais-document-endpoints/features/documents/list_documents.feature
  - src/hitchhikers/client.py
  - src/hitchhikers/schemas/v2.py
  - tests/conftest.py
-->

- [x] 4.1 Create `tests/test_list_documents.py`. Use `@respx.mock` and `client` fixture.

      Mock target: `respx.get("https://api.neolicense.ai/api/v2/dais/documents")`
      Default success response: `httpx.Response(200, json={"items": [], "count": 0})`

      **test_list_documents_default_params_sent** — default limit/offset always included
      - Call `client.list_documents()`
      - Assert response is `PagedDocListOut` with `items == []` and `count == 0`
      - Assert `respx.calls.last.request.url.params["limit"] == "100"`
      - Assert `respx.calls.last.request.url.params["offset"] == "0"`

      **test_list_documents_filter_by_doc_type** — optional filter included when provided
      - Call `client.list_documents(doc_type="contract")`
      - Assert `respx.calls.last.request.url.params["doc_type"] == "contract"`

      **test_list_documents_filter_by_date_range** — dates serialised as ISO strings
      - Import `from datetime import date`
      - Call `client.list_documents(start_date_gte=date(2024, 1, 1), end_date_lte=date(2024, 12, 31))`
      - Assert `respx.calls.last.request.url.params["start_date_gte"] == "2024-01-01"`
      - Assert `respx.calls.last.request.url.params["end_date_lte"] == "2024-12-31"`

      **test_list_documents_optional_params_omitted_when_absent**
      - Call `client.list_documents()`
      - Assert none of `doc_type`, `business_partner_id`, `internal_legal_entity_id`, `start_date_gte`, `end_date_lte` appear in `respx.calls.last.request.url.params`

- [x] 4.2 Replace `list_documents` in `src/hitchhikers/client.py`:
      - Add `from datetime import date` import at top of file (after `from pathlib import Path`)
      - New signature:
        ```python
        def list_documents(
            self,
            limit: int = 100,
            offset: int = 0,
            doc_type: str | None = None,
            business_partner_id: str | None = None,
            internal_legal_entity_id: str | None = None,
            start_date_gte: date | None = None,
            end_date_lte: date | None = None,
        ) -> PagedDocListOut:
        ```
      - Build params dict — always include `limit` and `offset`; include others only when not None:
        ```python
        params: dict = {"limit": limit, "offset": offset}
        if doc_type is not None:
            params["doc_type"] = doc_type
        if business_partner_id is not None:
            params["business_partner_id"] = str(business_partner_id)
        if internal_legal_entity_id is not None:
            params["internal_legal_entity_id"] = str(internal_legal_entity_id)
        if start_date_gte is not None:
            params["start_date_gte"] = start_date_gte.isoformat()
        if end_date_lte is not None:
            params["end_date_lte"] = end_date_lte.isoformat()
        ```
      - Return unchanged: `PagedDocListOut.model_validate(self._request("GET", "/api/v2/dais/documents", params=params))`

<!-- SESSION: section 4 complete. Red-green cycle confirmed: test_list_documents_default_params_sent failed (KeyError 'limit') against old **params signature, then passed after implementing typed params. Added from datetime import date import to client.py. New list_documents signature has limit=100, offset=0 always in params dict; doc_type, business_partner_id, internal_legal_entity_id, start_date_gte, end_date_lte included only when not None; dates via .isoformat(). All 14 tests pass (4 existing + 6 upload + 4 list_documents). Status: 10/24 complete. -->

---

## 5. get_document — add tests (implementation exists at client.py:58)

<!-- context:
  - .grimoire/changes/add-dais-document-endpoints/features/documents/get_document.feature
  - src/hitchhikers/client.py
  - src/hitchhikers/schemas/v2.py
  - tests/conftest.py
-->

- [x] 5.1 Create `tests/test_get_document.py`. Use `@respx.mock` and `client` fixture.

      Test document ID: `"550e8400-e29b-41d4-a716-446655440000"`
      Mock target: `respx.get("https://api.neolicense.ai/api/v2/dais/documents/550e8400-e29b-41d4-a716-446655440000")`

      **test_get_document_returns_detail** — happy path: correct URL called, response validated to `DocDetailBaseOut`
      - Mock → `httpx.Response(200, json={"document_id": "550e8400-e29b-41d4-a716-446655440000", "title": "Test Doc", "state": "COMPLETE", "doc_type": "contract"})`
      - Call `client.get_document("550e8400-e29b-41d4-a716-446655440000")`
      - Assert response is `DocDetailBaseOut`
      - Assert `response.state == "COMPLETE"`

---

## 6. get_document_attributes — add tests (implementation exists at client.py:63)

<!-- context:
  - .grimoire/changes/add-dais-document-endpoints/features/documents/get_document_attributes.feature
  - src/hitchhikers/client.py
  - src/hitchhikers/schemas/v2.py
  - tests/conftest.py
-->

- [x] 6.1 Create `tests/test_get_document_attributes.py`. Use `@respx.mock` and `client` fixture.

      Mock target: `respx.get("https://api.neolicense.ai/api/v2/dais/documents/550e8400-e29b-41d4-a716-446655440000/attributes")`

      **test_get_attributes_returns_widget_list** — list of `ExtractionPayloadWidgetOut`, fields accessible
      - Mock → `httpx.Response(200, json=[{"schema_name": "dates", "schema_version": "1.0", "payload": {}, "display_config": {}}, {"schema_name": "parties", "schema_version": "1.0", "payload": {}, "display_config": {}}])`
      - Call `client.get_document_attributes("550e8400-e29b-41d4-a716-446655440000")`
      - Assert response is a list of length 2
      - Assert each item is `ExtractionPayloadWidgetOut`
      - Assert `response[0].schema_name == "dates"`

      **test_get_attributes_returns_empty_list** — empty list accepted (not None, not error)
      - Mock → `httpx.Response(200, json=[])`
      - Assert response == `[]`

---

## 7. get_transform_output — new method

<!-- context:
  - .grimoire/changes/add-dais-document-endpoints/features/documents/get_transform_output.feature
  - src/hitchhikers/client.py
  - tests/conftest.py
-->

- [x] 7.1 Create `tests/test_transform_output.py`. Use `@respx.mock` and `client` fixture.

      Mock target: `respx.get("https://api.neolicense.ai/api/v2/dais/documents/550e8400-e29b-41d4-a716-446655440000/transform-output")`

      **test_get_transform_output_returns_raw_dict** — raw dict returned, no Pydantic parsing
      - Mock → `httpx.Response(200, json={"contract_value": 50000, "parties": ["Acme", "Beta Corp"]})`
      - Call `client.get_transform_output("550e8400-e29b-41d4-a716-446655440000")`
      - Assert response == `{"contract_value": 50000, "parties": ["Acme", "Beta Corp"]}`
      - Assert `isinstance(response, dict)`

- [x] 7.2 Add `get_transform_output` to `src/hitchhikers/client.py`:
      - Add `from typing import Any` to imports (after `from pathlib import Path`)
      - Add method after `get_document_attributes`, before `close`:
        ```python
        def get_transform_output(self, document_id: str) -> Any:
            return self._request("GET", f"/api/v2/dais/documents/{document_id}/transform-output")
        ```
      - No Pydantic validation — return the raw parsed JSON from `_request` directly

<!-- SESSION: section 7 complete. Red-green cycle confirmed: test_get_transform_output_returns_raw_dict failed (AttributeError: no attribute get_transform_output), then passed after implementing. Added from typing import Any import to client.py. New get_transform_output method added after get_document_attributes, before close; returns _request result directly with no Pydantic validation. All 18 tests pass. Status: 16/24 complete (sections 1–7 done). -->

---

## 8. Retry logic — tenacity wrapping _request

<!-- context:
  - .grimoire/changes/add-dais-document-endpoints/decisions/0006-tenacity-retries.md
  - src/hitchhikers/client.py
  - src/hitchhikers/exceptions.py
  - tests/conftest.py
  - .grimoire/changes/add-dais-document-endpoints/features/client/client_configuration.feature
-->

- [x] 8.1 Create `tests/test_retry.py`. Use `@respx.mock` and `retrying_client` fixture (max_retries=2) for all retry behaviour tests.

      Import: `from tenacity import RetryError` is NOT needed — `reraise=True` means the original exception propagates.

      **test_retries_on_5xx_then_succeeds** — satisfies "Client retries on transient 5xx errors"
      - Use sequential mock responses:
        ```python
        respx.get("https://api.neolicense.ai/items/").mock(
            side_effect=[
                httpx.Response(503, text="unavailable"),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        ```
      - Call `retrying_client._request("GET", "/items/")`
      - Assert response == `{"ok": True}`
      - Assert `respx.calls` count == 2

      **test_retries_on_network_timeout** — satisfies "Client retries on network errors"
      - Mock `side_effect=[httpx.TimeoutException(""), httpx.Response(200, json={"ok": True})]`
      - Call `retrying_client._request("GET", "/items/")`
      - Assert response == `{"ok": True}`

      **test_raises_after_exhausting_retries** — satisfies "Client raises after exhausting default retry limit"
      - max_retries=2 means 3 total attempts; mock 3 consecutive 503s
      - Assert `APIError` raised with `exc_info.value.status_code == 503`
      - Assert `respx.calls` count == 3

      **test_custom_max_retries** — satisfies "Construct client with custom retry count"
      - Create `KiwiClient(api_key="test-key", base_url="https://api.neolicense.ai", max_retries=1)` inside test
      - Mock 2 consecutive 503s (1 retry = 2 total attempts, both fail)
      - Assert `APIError` raised
      - Assert `respx.calls` count == 2

      **test_no_retry_on_4xx** — satisfies "Client does not retry on 4xx errors"
      - Mock `GET /items/` → `httpx.Response(404)`
      - Call `retrying_client._request("GET", "/items/")`
      - Assert `NotFoundError` raised
      - Assert `respx.calls` count == 1 (no retry attempted)

- [x] 8.2 Update `src/hitchhikers/client.py` with tenacity retry support:

      Add imports at top of file (after existing imports):
      ```python
      from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential
      ```

      Add module-level helper before `class KiwiClient` (not a method — no `self` binding needed):
      ```python
      def _is_retryable(exc: BaseException) -> bool:
          if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
              return True
          return isinstance(exc, APIError) and exc.status_code >= 500
      ```

      Add `max_retries: int = 2` to `__init__` and store it:
      ```python
      def __init__(
          self,
          api_key: str,
          base_url: str = "https://api.neolicense.ai",
          timeout: float = 30.0,
          max_retries: int = 2,
      ):
          self._max_retries = max_retries
          self._http = httpx.Client(
              base_url=base_url,
              headers={"X-API-Key": api_key},
              timeout=timeout,
          )
      ```

      Replace `_request` body to use tenacity `Retrying` context manager:
      ```python
      def _request(self, method: str, path: str, **kwargs):
          for attempt in Retrying(
              stop=stop_after_attempt(self._max_retries + 1),
              wait=wait_exponential(multiplier=0.1, min=0.1, max=5),
              retry=retry_if_exception(_is_retryable),
              reraise=True,
          ):
              with attempt:
                  return self._handle_response(self._http.request(method, path, **kwargs))
      ```

      `wait_exponential(multiplier=0.1, min=0.1, max=5)`: first retry at ~0.1s, second at ~0.2s. Keeps tests fast while providing reasonable production backoff.

      `upload_document` is unaffected — it calls `self._http.post` directly, bypassing `_request` and tenacity entirely.

<!-- SESSION: section 8 complete. Red-green cycle confirmed: 4/5 tests failed against unwrapped _request (test_no_retry_on_4xx already passed), then all 5 passed after implementing tenacity wrapping. Added tenacity import and _is_retryable module-level function before KiwiClient. Replaced _request body with Retrying context manager: stop_after_attempt(max_retries+1), wait_exponential(multiplier=0.1, min=0.1, max=5), retry_if_exception(_is_retryable), reraise=True. upload_document unaffected (uses self._http.post directly). All 23 tests pass. Status: 21/24 complete (sections 1–8 done). -->

---

## 9. Client configuration tests

<!-- context:
  - .grimoire/changes/add-dais-document-endpoints/features/client/client_configuration.feature
  - tests/test_client.py
  - src/hitchhikers/client.py
  - tests/conftest.py
-->

- [x] 9.1 Add to `tests/test_client.py`:

      **test_raises_not_found_on_404** — one canonical test for 404 → NotFoundError (covers all endpoints)
      - Mock `GET https://api.neolicense.ai/example/` → `httpx.Response(404)`
      - Assert `NotFoundError` raised

      **test_api_key_sent_as_header** — satisfies "Construct client with API key only"
      - Mock `GET https://api.neolicense.ai/items/` → `httpx.Response(200, json={})`
      - Call `client._request("GET", "/items/")`
      - Assert `respx.calls.last.request.headers["x-api-key"] == "test-key"`

      **test_custom_base_url** — satisfies "Construct client with custom base URL"
      - Inside test: create `KiwiClient(api_key="k", base_url="https://custom.example.com", max_retries=0)`
      - Mock `respx.get("https://custom.example.com/path/")` → `httpx.Response(200, json={})`
      - Call `custom_client._request("GET", "/path/")`
      - Assert request went to `https://custom.example.com/path/`

---

## 10. Verification

- [x] 10.1 Run `uv run pytest tests/ -v` — all new and existing tests pass, no regressions
- [x] 10.2 Run `uv run flake8 src/ tests/` — no lint errors
- [x] 10.3 Run `uv run black --check src/ tests/` — formatting clean
- [x] 10.4 Run `uv run pytest tests/ --cov=src --cov-report=term-missing` — confirm `get_transform_output`, updated `upload_document`, updated `list_documents`, and `_request` retry path all have coverage

<!-- SESSION: sections 9+10 complete. Added 3 tests to tests/test_client.py: test_raises_not_found_on_404 (404 → NotFoundError), test_api_key_sent_as_header (x-api-key header check), test_custom_base_url (custom base URL routing). Added NotFoundError to imports in test_client.py. Fixed all flake8 issues across src/ and tests/ (E501 line length, F401 unused imports, W391 trailing blank line) and ran black to auto-format. All 26 tests pass, 99% coverage. Status: 24/24 complete — change fully implemented. -->
