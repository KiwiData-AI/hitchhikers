import httpx
import respx
from hitchhikers.schemas.v2 import DocDetailBaseOut

DOC_ID = "550e8400-e29b-41d4-a716-446655440000"
DOC_URL = f"https://api.neolicense.ai/api/v2/dais/documents/{DOC_ID}"


@respx.mock
def test_get_document_returns_detail(client):
    respx.get(DOC_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "document_id": DOC_ID,
                "title": "Test Doc",
                "state": "COMPLETE",
                "doc_type": "contract",
            },
        )
    )

    response = client.get_document(DOC_ID)

    assert isinstance(response, DocDetailBaseOut)
    assert response.state == "COMPLETE"
