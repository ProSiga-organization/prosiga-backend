from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from app.main import app  
from app import deps
from app import model
from app.conftest import mock_auth_coordenador, mock_auth_aluno

def test_get_all_periodos_letivos_vazio(client: TestClient):
    """
    Testa GET /periodos-letivos/ (sem autenticação)
    Deve retornar uma lista vazia no início.
    """
    response = client.get("/periodos-letivos")
    assert response.status_code == 200
    assert response.json() == []

def test_create_periodo_letivo_como_coordenador(client: TestClient, mock_coordenador: model.Coordenador):
    """
    Testa POST /periodos-letivos/ (Autenticado como Coordenador)
    Deve criar o período com sucesso (201).
    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(mock_coordenador)
    
    payload = {
        "ano": 2025,
        "semestre": 1,
        "inicio_matricula": "2025-01-01",
        "fim_matricula": "2025-01-10",
        "fim_trancamento": "2025-03-01"
    }
    
    response = client.post("/periodos-letivos/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["ano"] == 2025
    assert data["semestre"] == 1
    assert data["id"] is not None

def test_create_periodo_letivo_como_aluno(client: TestClient, mock_aluno: model.Aluno):
    """
    Testa POST /periodos-letivos/ (Autenticado como Aluno)
    Deve falhar com erro 403 (Forbidden).
    """
    def mock_get_current_user():
        return mock_aluno
    
    app.dependency_overrides[deps.get_current_user] = mock_get_current_user
    
    payload = {
        "ano": 2026,
        "semestre": 1,
        "inicio_matricula": "2026-01-01",
        "fim_matricula": "2026-01-10",
        "fim_trancamento": "2026-03-01"
    }
    
    response = client.post("/periodos-letivos/", json=payload)
    
    assert response.status_code == 403
    assert response.json()["detail"] == "Acesso negado: Apenas para coordenadores."

def test_get_periodo_letivo_by_id(client: TestClient, db_session: Session, mock_coordenador: model.Coordenador):
    """
    Testa GET /periodos-letivos/{id}
    Primeiro cria um período, depois busca por ele.
    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(mock_coordenador)
    
    payload_criacao = {
        "ano": 2025,
        "semestre": 2,
        "inicio_matricula": "2025-06-01",
        "fim_matricula": "2025-06-10",
        "fim_trancamento": "2025-08-01"
    }
    response_criacao = client.post("/periodos-letivos/", json=payload_criacao)
    assert response_criacao.status_code == 201
    id_criado = response_criacao.json()["id"]

    app.dependency_overrides.pop(deps.get_current_coordenador, None)
    response_busca = client.get(f"/periodos-letivos/{id_criado}")
    
    assert response_busca.status_code == 200
    data = response_busca.json()
    assert data["id"] == id_criado
    assert data["ano"] == 2025
    assert data["semestre"] == 2

def test_get_periodo_letivo_by_id_not_found(client: TestClient):
    """
    Testa GET /periodos-letivos/{id} para um ID que não existe
    Deve retornar 404 (Not Found).
    """
    response = client.get("/periodos-letivos/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Período letivo não encontrado."