from fastapi.testclient import TestClient

from repolens.api import create_app
from repolens.models import GraphDocument


def test_local_api_serves_packaged_web_app() -> None:
    response = TestClient(create_app(GraphDocument())).get("/")

    assert response.status_code == 200
    assert "RepoLens" in response.text
