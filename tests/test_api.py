from fastapi.testclient import TestClient

from src.api.main import app


def test_health():
    resposta = TestClient(app).get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
