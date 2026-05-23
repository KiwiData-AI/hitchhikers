import httpx
import pytest
import respx

from hitchhikers import KiwiClient
from hitchhikers.exceptions import APIError, NotFoundError


@respx.mock
def test_retries_on_5xx_then_succeeds(retrying_client):
    respx.get("https://api.neolicense.ai/items/").mock(
        side_effect=[
            httpx.Response(503, text="unavailable"),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    response = retrying_client._request("GET", "/items/")
    assert response == {"ok": True}
    assert len(respx.calls) == 2


@respx.mock
def test_retries_on_network_timeout(retrying_client):
    respx.get("https://api.neolicense.ai/items/").mock(
        side_effect=[
            httpx.TimeoutException(""),
            httpx.Response(200, json={"ok": True}),
        ]
    )
    response = retrying_client._request("GET", "/items/")
    assert response == {"ok": True}


@respx.mock
def test_raises_after_exhausting_retries(retrying_client):
    respx.get("https://api.neolicense.ai/items/").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(503),
        ]
    )
    with pytest.raises(APIError) as exc_info:
        retrying_client._request("GET", "/items/")
    assert exc_info.value.status_code == 503
    assert len(respx.calls) == 3


@respx.mock
def test_custom_max_retries():
    custom_client = KiwiClient(
        api_key="test-key", base_url="https://api.neolicense.ai", max_retries=1
    )
    respx.get("https://api.neolicense.ai/items/").mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(503),
        ]
    )
    with pytest.raises(APIError):
        custom_client._request("GET", "/items/")
    assert len(respx.calls) == 2


@respx.mock
def test_no_retry_on_4xx(retrying_client):
    respx.get("https://api.neolicense.ai/items/").mock(return_value=httpx.Response(404))
    with pytest.raises(NotFoundError):
        retrying_client._request("GET", "/items/")
    assert len(respx.calls) == 1
