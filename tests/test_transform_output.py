import httpx
import respx

DOC_ID = "550e8400-e29b-41d4-a716-446655440000"
BASE = "https://api.neolicense.ai"


@respx.mock
def test_get_transform_output_returns_raw_dict(client):
    url = f"{BASE}/api/v2/dais/documents/{DOC_ID}/transform-output"
    respx.get(url).mock(
        return_value=httpx.Response(
            200, json={"contract_value": 50000, "parties": ["Acme", "Beta Corp"]}
        )
    )

    response = client.get_transform_output(DOC_ID)

    assert response == {"contract_value": 50000, "parties": ["Acme", "Beta Corp"]}
    assert isinstance(response, dict)
