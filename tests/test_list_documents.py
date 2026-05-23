import httpx
import respx
from datetime import date

from hitchhikers.schemas.v2 import PagedDocListOut


@respx.mock
def test_list_documents_default_params_sent(client):
    respx.get("https://api.neolicense.ai/api/v2/dais/documents").mock(
        return_value=httpx.Response(200, json={"items": [], "count": 0})
    )
    response = client.list_documents()
    assert isinstance(response, PagedDocListOut)
    assert response.items == []
    assert response.count == 0
    assert respx.calls.last.request.url.params["limit"] == "100"
    assert respx.calls.last.request.url.params["offset"] == "0"


@respx.mock
def test_list_documents_filter_by_doc_type(client):
    respx.get("https://api.neolicense.ai/api/v2/dais/documents").mock(
        return_value=httpx.Response(200, json={"items": [], "count": 0})
    )
    client.list_documents(doc_type="contract")
    assert respx.calls.last.request.url.params["doc_type"] == "contract"


@respx.mock
def test_list_documents_filter_by_date_range(client):
    respx.get("https://api.neolicense.ai/api/v2/dais/documents").mock(
        return_value=httpx.Response(200, json={"items": [], "count": 0})
    )
    client.list_documents(
        start_date_gte=date(2024, 1, 1), end_date_lte=date(2024, 12, 31)
    )
    assert respx.calls.last.request.url.params["start_date_gte"] == "2024-01-01"
    assert respx.calls.last.request.url.params["end_date_lte"] == "2024-12-31"


@respx.mock
def test_list_documents_optional_params_omitted_when_absent(client):
    respx.get("https://api.neolicense.ai/api/v2/dais/documents").mock(
        return_value=httpx.Response(200, json={"items": [], "count": 0})
    )
    client.list_documents()
    params = respx.calls.last.request.url.params
    assert "doc_type" not in params
    assert "business_partner_id" not in params
    assert "internal_legal_entity_id" not in params
    assert "start_date_gte" not in params
    assert "end_date_lte" not in params
