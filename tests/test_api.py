"""Tests for the FastAPI service scaffold."""

from fastapi.testclient import TestClient

from services.api.main import app


client = TestClient(app)


def test_root_endpoint() -> None:
    """The root endpoint should return the API name."""
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "Scriptorium API"


def test_health_endpoint() -> None:
    """The health endpoint should return ok status."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_project_endpoint() -> None:
    """The project endpoint should expose project metadata."""
    response = client.get("/project")

    assert response.status_code == 200

    data = response.json()
    assert data["project_name"] == "scriptorium"
    assert data["visible_watermark_enabled"] is True
