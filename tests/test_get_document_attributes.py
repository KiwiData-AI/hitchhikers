import httpx
import respx
from hitchhikers.schemas.v2 import ExtractionPayloadWidgetOut

DOC_ID = "550e8400-e29b-41d4-a716-446655440000"
ATTRS_URL = f"https://api.neolicense.ai/api/v2/dais/documents/{DOC_ID}/attributes"


@respx.mock
def test_get_attributes_returns_widget_list(client):
    respx.get(ATTRS_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "schema_name": "dates",
                    "schema_version": "1.0",
                    "payload": {},
                    "display_config": {},
                },
                {
                    "schema_name": "parties",
                    "schema_version": "1.0",
                    "payload": {},
                    "display_config": {},
                },
            ],
        )
    )

    response = client.get_document_attributes(DOC_ID)

    assert len(response) == 2
    assert all(isinstance(item, ExtractionPayloadWidgetOut) for item in response)
    assert response[0].schema_name == "dates"


@respx.mock
def test_get_attributes_returns_empty_list(client):
    respx.get(ATTRS_URL).mock(return_value=httpx.Response(200, json=[]))

    response = client.get_document_attributes(DOC_ID)

    assert response == []
