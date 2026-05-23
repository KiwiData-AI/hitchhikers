from datetime import date
from pathlib import Path
from typing import Any
import httpx
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential
from .schemas.v1 import DocumentSchema
from .schemas.v2 import DocDetailBaseOut, ExtractionPayloadWidgetOut, PagedDocListOut
from .exceptions import APIError, AuthenticationError, NotFoundError


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    return isinstance(exc, APIError) and exc.status_code >= 500


class KiwiClient:
    """HTTP client for the Kiwi document processing API."""

    # Cloudflare challenge-page mitigation — plain httpx UA triggers bot detection.
    _DEFAULT_UA = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.neolicense.ai",
        timeout: float = 30.0,
        max_retries: int = 2,
        user_agent: str | None = None,
    ):
        """
        :param api_key: API key, sent as ``X-API-Key`` header.
        :param base_url: API base URL.
        :param timeout: Request timeout in seconds.
        :param max_retries: Retry attempts on 5xx/network errors. 0 disables retries.
        :param user_agent: Override the default User-Agent header.
        """
        self._max_retries = max_retries
        self._http = httpx.Client(
            base_url=base_url,
            headers={
                "X-API-Key": api_key,
                "User-Agent": (
                    user_agent if user_agent is not None else self._DEFAULT_UA
                ),
            },
            timeout=timeout,
        )

    def _handle_response(self, response: httpx.Response):
        if response.status_code == 401:
            raise AuthenticationError("Invalid or expired API key")
        if response.status_code == 404:
            raise NotFoundError(f"Resource not found: {response.url}")
        if response.status_code >= 400:
            raise APIError(response.status_code, response.text)
        response.raise_for_status()
        return response.json()

    def _request(self, method: str, path: str, **kwargs) -> Any:
        for attempt in Retrying(
            stop=stop_after_attempt(self._max_retries + 1),
            wait=wait_exponential(multiplier=0.1, min=0.1, max=5),
            retry=retry_if_exception(_is_retryable),
            reraise=True,
        ):
            with attempt:
                return self._handle_response(self._http.request(method, path, **kwargs))

    def upload_document(
        self,
        file_path: str | Path,
        title: str | None = None,
        doc_type: str | None = None,
        external_id: str | None = None,
    ) -> DocumentSchema:
        """Upload a document for processing.

        :param file_path: Path to the file to upload.
        :param title: Document title. Defaults to the filename.
        :param doc_type: Document type name. Optional but recommended.
        :param external_id: Caller's system record ID. Recommended for idempotency.
        :returns: Created document record.
        :raises APIError: On duplicate submission or other 4xx errors.
        """
        path = Path(file_path)
        resolved_title = title if title is not None else path.name
        data: dict = {"title": resolved_title}
        if doc_type is not None:
            data["doctype_name"] = doc_type
        if external_id is not None:
            data["external_id"] = external_id
        with path.open("rb") as f:
            response = self._http.post(
                "/api/v1/dais/document/",
                files={"file": (path.name, f)},
                data=data,
            )
        return DocumentSchema.model_validate(self._handle_response(response))

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
        """List documents with optional filters.

        :param limit: Max results to return.
        :param offset: Pagination offset.
        :param doc_type: Filter by document type.
        :param business_partner_id: Filter by business partner UUID.
        :param internal_legal_entity_id: Filter by legal entity UUID.
        :param start_date_gte: Filter documents with start date on or after this date.
        :param end_date_lte: Filter documents with end date on or before this date.
        :returns: Paged list of documents.
        """
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
        return PagedDocListOut.model_validate(
            self._request("GET", "/api/v2/dais/documents", params=params)
        )

    def get_document(self, document_id: str) -> DocDetailBaseOut:
        """Fetch document state and metadata.

        :param document_id: Document UUID.
        :returns: Document detail.
        :raises NotFoundError: If the document does not exist.
        """
        return DocDetailBaseOut.model_validate(
            self._request("GET", f"/api/v2/dais/documents/{document_id}")
        )

    def get_document_attributes(
        self, document_id: str
    ) -> list[ExtractionPayloadWidgetOut]:
        """Fetch extraction payloads for a document.

        :param document_id: Document UUID.
        :returns: List of extracted attribute widgets. Empty if processing incomplete.
        :raises NotFoundError: If the document does not exist.
        """
        return [
            ExtractionPayloadWidgetOut.model_validate(item)
            for item in self._request(
                "GET", f"/api/v2/dais/documents/{document_id}/attributes"
            )
        ]

    def get_transform_output(self, document_id: str) -> Any:
        """Fetch the client transform output for a document.

        The shape varies by document type and configured transform.
        Callers are responsible for parsing against their own schema.

        :param document_id: Document UUID.
        :returns: Raw transform output. Structure is client-defined.
        :raises NotFoundError: If the document does not exist.
        """
        return self._request(
            "GET", f"/api/v2/dais/documents/{document_id}/transform-output"
        )

    def close(self):
        """Close the underlying HTTP connection."""
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
