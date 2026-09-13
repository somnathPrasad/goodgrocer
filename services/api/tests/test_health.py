import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://goodgrocer:goodgrocer@localhost:5432/goodgrocer_test",
)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
