from pathlib import Path
import httpx
from .schemas.v1 import DocumentSchema
from .schemas.v2 import DocDetailBaseOut, ExtractionPayloadWidgetOut, PagedDocListOut
from .exceptions import APIError, AuthenticationError, NotFoundError


class KiwiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.neolicense.ai",
        timeout: float = 30.0,
    ):
        self._http = httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": api_key},
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

    def _request(self, method: str, path: str, **kwargs):
        return self._handle_response(self._http.request(method, path, **kwargs))

    def upload_document(
        self,
        file_path: str | Path,
        title: str,
        doc_type: str,
        external_id: str | None = None,
    ) -> DocumentSchema:
        path = Path(file_path)
        data: dict = {"title": title, "doctype_name": doc_type}
        if external_id is not None:
            data["external_id"] = external_id
        with path.open("rb") as f:
            response = self._http.post(
                "/api/v1/dais/document/",
                files={"file": (path.name, f)},
                data=data,
            )
        return DocumentSchema.model_validate(self._handle_response(response))

    def list_documents(self, **params) -> PagedDocListOut:
        return PagedDocListOut.model_validate(
            self._request("GET", "/api/v2/dais/documents", params=params)
        )

    def get_document(self, document_id: str) -> DocDetailBaseOut:
        return DocDetailBaseOut.model_validate(
            self._request("GET", f"/api/v2/dais/documents/{document_id}")
        )

    def get_document_attributes(
        self, document_id: str
    ) -> list[ExtractionPayloadWidgetOut]:
        return [
            ExtractionPayloadWidgetOut.model_validate(item)
            for item in self._request(
                "GET", f"/api/v2/dais/documents/{document_id}/attributes"
            )
        ]

    def close(self):
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
