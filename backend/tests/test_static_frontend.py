from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_serves_frontend_index_html():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_health_endpoint_still_works_after_static_mount():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
