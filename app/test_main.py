from fastapi.testclient import TestClient
import pytest

def test_health_check(client: TestClient):
    """
    Testa o endpoint de health check (GET /).
    Não requer autenticação nem banco de dados.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}