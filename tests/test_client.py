import httpx
import pytest
import respx
from hitchhikers import APIError, AuthenticationError, KiwiClient


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
