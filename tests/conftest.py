import pytest
from hitchhikers import KiwiClient


@pytest.fixture
def client():
    return KiwiClient(api_key="test-key", base_url="https://api.neolicense.ai")
