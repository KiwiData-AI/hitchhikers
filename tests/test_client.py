import httpx
import pytest
import respx
from hitchhikers import APIError, AuthenticationError, KiwiClient, NotFoundError


@respx.mock
def test_client_context_manager():
    with KiwiClient(api_key="test-key", base_url="https://api.neolicense.ai") as client:
        assert client is not None


@respx.mock
def test_raises_auth_error_on_401(client):
    respx.get("https://api.neolicense.ai/example/").mock(
        return_value=httpx.Response(401)
    )
    with pytest.raises(AuthenticationError):
        client._request("GET", "/example/")


@respx.mock
def test_raises_api_error_on_500(client):
    respx.get("https://api.neolicense.ai/example/").mock(
        return_value=httpx.Response(500, text="Server Error")
    )
    with pytest.raises(APIError) as exc_info:
        client._request("GET", "/example/")
    assert exc_info.value.status_code == 500


@respx.mock
def test_successful_get_returns_json(client):
    respx.get("https://api.neolicense.ai/items/").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    data = client._request("GET", "/items/")
    assert data == {"results": []}


@respx.mock
def test_raises_not_found_on_404(client):
    respx.get("https://api.neolicense.ai/example/").mock(
        return_value=httpx.Response(404)
    )
    with pytest.raises(NotFoundError):
        client._request("GET", "/example/")


@respx.mock
def test_api_key_sent_as_header(client):
    respx.get("https://api.neolicense.ai/items/").mock(
        return_value=httpx.Response(200, json={})
    )
    client._request("GET", "/items/")
    assert respx.calls.last.request.headers["x-api-key"] == "test-key"


@respx.mock
def test_custom_base_url():
    custom_client = KiwiClient(
        api_key="k", base_url="https://custom.example.com", max_retries=0
    )
    respx.get("https://custom.example.com/path/").mock(
        return_value=httpx.Response(200, json={})
    )
    custom_client._request("GET", "/path/")
    assert respx.calls.last.request.url.host == "custom.example.com"
