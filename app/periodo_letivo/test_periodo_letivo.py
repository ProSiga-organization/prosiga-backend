from datetime import date
from unittest.mock import MagicMock, patch

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import model

AUTH_MOCK_PATH = "app.deps.requests.get"


def mock_auth_response(user_model):
    """Cria um mock de resposta bem-sucedida do serviço de autenticação."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"email": user_model.email, "id": user_model.id}
    mock_response.raise_for_status.return_value = None
    return mock_response


def mock_auth_failure():
    """Cria um mock de resposta de falha (ex: token inválido) do serviço de autenticação."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {
        "detail": "Não foi possível validar as credenciais com o serviço de autenticação."
    }
    mock_response.raise_for_status.side_effect = requests.exceptions.RequestException(
        "Mocked request failure"
    )
    return mock_response


def test_get_all_periodos_letivos_vazio(client: TestClient, mock_aluno: model.Aluno):
    """
    Testa GET /periodos-letivos/ (com autenticação)
    Deve retornar uma lista vazia no início.
    """
    headers = {"Authorization": "Bearer fake-token"}
    
    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)):
        response = client.get("/periodos-letivos", headers=headers)
    
    assert response.status_code == 200
    assert response.json() == []


def test_create_periodo_letivo_como_coordenador(
    client: TestClient, mock_coordenador: model.Coordenador
):
    """
    Testa POST /periodos-letivos/ (Autenticado como Coordenador)
    Deve criar o período com sucesso (201).
    """
    payload = {
        "ano": 2025,
        "semestre": 1,
        "inicio_matricula": "2025-01-01",
        "fim_matricula": "2025-01-10",
        "fim_trancamento": "2025-03-01",
    }
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.post("/periodos-letivos/", json=payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["ano"] == 2025
    assert data["semestre"] == 1
    assert data["id"] is not None


@pytest.mark.parametrize(
    "user_fixture, esperado_status, esperado_detalhe",
    [
        ("mock_aluno", 403, "Acesso negado: Apenas para coordenadores."),
        ("mock_professor", 403, "Acesso negado: Apenas para coordenadores."),
        (
            "token_invalido",
            401,
            "Não foi possível validar as credenciais com o serviço de autenticação.",
        ),
    ],
)
def test_create_periodo_letivo_sem_permissao(
    client: TestClient,
    user_fixture: str,
    esperado_status: int,
    esperado_detalhe: str,
    request,
):
    """
    Testa (de forma parametrizada) que Alunos, Professores ou usuários
    com token inválido não podem criar períodos letivos.
    """
    headers = {"Authorization": "Bearer fake-token"}
    payload = {
        "ano": 2026,
        "semestre": 1,
        "inicio_matricula": "2026-01-01",
        "fim_matricula": "2026-01-10",
        "fim_trancamento": "2026-03-01",
    }

    mock_user = None
    if user_fixture in ("mock_aluno", "mock_professor"):
        mock_user = request.getfixturevalue(user_fixture)
        mock_return = mock_auth_response(mock_user)
    else:
        mock_return = mock_auth_failure()

    with patch(AUTH_MOCK_PATH, return_value=mock_return):
        response = client.post("/periodos-letivos/", json=payload, headers=headers)

    assert response.status_code == esperado_status
    assert esperado_detalhe in response.json()["detail"]


def test_get_periodo_letivo_by_id(
    client: TestClient, db_session: Session, mock_coordenador: model.Coordenador
):
    """
    Testa GET /periodos-letivos/{id}
    Primeiro cria um período, depois busca por ele.
    """
    payload_criacao = {
        "ano": 2025,
        "semestre": 2,
        "inicio_matricula": "2025-06-01",
        "fim_matricula": "2025-06-10",
        "fim_trancamento": "2025-08-01",
    }
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response_criacao = client.post(
            "/periodos-letivos/", json=payload_criacao, headers=headers
        )

    assert response_criacao.status_code == 201
    id_criado = response_criacao.json()["id"]

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response_busca = client.get(f"/periodos-letivos/{id_criado}", headers=headers)

    assert response_busca.status_code == 200
    data = response_busca.json()
    assert data["id"] == id_criado
    assert data["ano"] == 2025
    assert data["semestre"] == 2


def test_get_periodo_letivo_by_id_not_found(client: TestClient, mock_aluno: model.Aluno):
    """
    Testa GET /periodos-letivos/{id} para um ID que não existe
    Deve retornar 404 (Not Found).
    """
    headers = {"Authorization": "Bearer fake-token"}
    
    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)):
        response = client.get("/periodos-letivos/999", headers=headers)

    assert response.status_code == 404
    assert response.json()["detail"] == "Período letivo não encontrado."


@pytest.mark.parametrize(
    "relatorio_endpoint", ["relatorio-ocupacao", "relatorio-turmas-professor"]
)
def test_coordenador_gera_relatorios_pdf(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    setup_matricula_existente: dict,
    relatorio_endpoint: str,
):
    """
    Testa US-012: Coordenador gera PDFs de relatórios do período.
    - /relatorio-ocupacao
    - /relatorio-turmas-professor
    """
    periodo = setup_matricula_existente["periodo"]
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.get(
            f"/periodos-letivos/{periodo.id}/{relatorio_endpoint}", headers=headers
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert (
        f"{relatorio_endpoint.replace('-', '_')}_{periodo.ano}_{periodo.semestre}.pdf"
        in response.headers["content-disposition"]
    )
    assert len(response.content) > 0


def test_coordenador_atualiza_periodo_letivo(
    client: TestClient, db_session: Session, mock_coordenador: model.Coordenador
):
    """
    Testa US-009: Coordenador atualiza um período letivo existente.
    """
    periodo = model.PeriodoLetivo(
        ano=2026,
        semestre=1,
        inicio_matricula=date(2026, 1, 1),
        fim_matricula=date(2026, 1, 10),
        fim_trancamento=date(2026, 3, 1),
    )
    db_session.add(periodo)
    db_session.commit()

    payload_atualizacao = {
        "ano": 2026,
        "semestre": 1,
        "inicio_matricula": "2026-01-05",
        "fim_matricula": "2026-01-15",
        "fim_trancamento": "2026-03-10",
    }
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.put(
            f"/periodos-letivos/{periodo.id}",
            json=payload_atualizacao,
            headers=headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["inicio_matricula"] == "2026-01-05"
    assert data["fim_trancamento"] == "2026-03-10"

    db_session.refresh(periodo)
    assert periodo.inicio_matricula == date(2026, 1, 5)


def test_coordenador_deleta_periodo_letivo(
    client: TestClient, db_session: Session, mock_coordenador: model.Coordenador
):
    """
    Testa US-009: Coordenador deleta um período letivo.
    """
    periodo = model.PeriodoLetivo(
        ano=2027,
        semestre=1,
        inicio_matricula=date(2027, 1, 1),
        fim_matricula=date(2027, 1, 10),
        fim_trancamento=date(2027, 3, 1),
    )
    db_session.add(periodo)
    db_session.commit()
    id_periodo = periodo.id

    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.delete(f"/periodos-letivos/{id_periodo}", headers=headers)

    assert response.status_code == 204

    periodo_db = db_session.get(model.PeriodoLetivo, id_periodo)
    assert periodo_db is None
