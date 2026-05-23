import httpx
import respx
from hitchhikers.schemas.v1 import DocumentSchema

UPLOAD_URL = "https://api.neolicense.ai/api/v1/dais/document/"
VALID_RESPONSE = {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "contract.pdf",
    "can_delete": False,
}


@respx.mock
def test_upload_title_defaults_to_filename(client, tmp_path):
    (tmp_path / "contract.pdf").write_bytes(b"fake pdf content")
    respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))

    response = client.upload_document(file_path=tmp_path / "contract.pdf")

    content = respx.calls.last.request.content.decode()
    assert 'name="title"' in content
    assert "contract.pdf" in content
    assert isinstance(response, DocumentSchema)


@respx.mock
def test_upload_explicit_title(client, tmp_path):
    (tmp_path / "contract.pdf").write_bytes(b"fake pdf content")
    respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))

    response = client.upload_document(
        file_path=tmp_path / "contract.pdf", title="My Contract"
    )

    content = respx.calls.last.request.content.decode()
    assert "My Contract" in content
    assert isinstance(response, DocumentSchema)


@respx.mock
def test_upload_with_doc_type(client, tmp_path):
    (tmp_path / "contract.pdf").write_bytes(b"fake pdf content")
    respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))

    client.upload_document(file_path=tmp_path / "contract.pdf", doc_type="contract")

    content = respx.calls.last.request.content.decode()
    assert 'name="doctype_name"' in content
    assert "contract" in content


@respx.mock
def test_upload_without_doc_type(client, tmp_path):
    (tmp_path / "contract.pdf").write_bytes(b"fake pdf content")
    respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))

    response = client.upload_document(file_path=tmp_path / "contract.pdf")

    content = respx.calls.last.request.content.decode()
    assert "doctype_name" not in content
    assert isinstance(response, DocumentSchema)


@respx.mock
def test_upload_with_external_id(client, tmp_path):
    (tmp_path / "contract.pdf").write_bytes(b"fake pdf content")
    respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))

    client.upload_document(file_path=tmp_path / "contract.pdf", external_id="CRM-12345")

    content = respx.calls.last.request.content.decode()
    assert 'name="external_id"' in content
    assert "CRM-12345" in content


@respx.mock
def test_upload_without_external_id(client, tmp_path):
    (tmp_path / "contract.pdf").write_bytes(b"fake pdf content")
    respx.post(UPLOAD_URL).mock(return_value=httpx.Response(200, json=VALID_RESPONSE))

    client.upload_document(file_path=tmp_path / "contract.pdf")

    content = respx.calls.last.request.content.decode()
    assert "external_id" not in content
