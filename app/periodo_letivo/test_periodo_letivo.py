from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import deps, model
from app.conftest import mock_auth_coordenador
from app.main import app


def test_get_all_periodos_letivos_vazio(client: TestClient):
    """
    Testa GET /periodos-letivos/ (sem autenticação)
    Deve retornar uma lista vazia no início.
    """
    response = client.get("/periodos-letivos")
    assert response.status_code == 200
    assert response.json() == []


def test_create_periodo_letivo_como_coordenador(
    client: TestClient, mock_coordenador: model.Coordenador
):
    """
    Testa POST /periodos-letivos/ (Autenticado como Coordenador)
    Deve criar o período com sucesso (201).
    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )

    payload = {
        "ano": 2025,
        "semestre": 1,
        "inicio_matricula": "2025-01-01",
        "fim_matricula": "2025-01-10",
        "fim_trancamento": "2025-03-01",
    }

    response = client.post("/periodos-letivos/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["ano"] == 2025
    assert data["semestre"] == 1
    assert data["id"] is not None


@pytest.mark.parametrize(
    "perfil, mock_user_fixture, esperado_status, esperado_detalhe",
    [
        ("aluno", "mock_aluno", 403, "Acesso negado: Apenas para coordenadores."),
        (
            "professor",
            "mock_professor",
            403,
            "Acesso negado: Apenas para coordenadores.",
        ),
        (
            "token_invalido",
            None,
            401,
            "Não foi possível validar as credenciais com o serviço de autenticação.",
        ),
    ],
)
def test_create_periodo_letivo_sem_permissao(
    client: TestClient,
    perfil: str,
    mock_user_fixture: str | None,
    esperado_status: int,
    esperado_detalhe: str,
    request,
):
    """
    Testa (de forma parametrizada) que Alunos, Professores ou usuários
    com token inválido não podem criar períodos letivos.
    """
    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_coordenador, None)
    headers = {}

    if perfil == "aluno" or perfil == "professor":
        mock_user = request.getfixturevalue(mock_user_fixture)

        def mock_get_current_user():
            return mock_user

        app.dependency_overrides[deps.get_current_user] = mock_get_current_user

        headers = {"Authorization": "Bearer mock-token"}

    elif perfil == "token_invalido":
        headers = {"Authorization": "Bearer token-que-vai-falhar"}

    payload = {
        "ano": 2026,
        "semestre": 1,
        "inicio_matricula": "2026-01-01",
        "fim_matricula": "2026-01-10",
        "fim_trancamento": "2026-03-01",
    }
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
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )

    payload_criacao = {
        "ano": 2025,
        "semestre": 2,
        "inicio_matricula": "2025-06-01",
        "fim_matricula": "2025-06-10",
        "fim_trancamento": "2025-08-01",
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


def test_coordenador_gera_relatorio_ocupacao_pdf(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    setup_matricula_existente: dict,
):
    """
    Testa US-012: Coordenador gera PDF de Ocupação de Vagas.

    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )
    periodo = setup_matricula_existente["periodo"]
    response = client.get(f"/periodos-letivos/{periodo.id}/relatorio-ocupacao")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert (
        f"relatorio_ocupacao_{periodo.ano}_{periodo.semestre}.pdf"
        in response.headers["content-disposition"]
    )
    assert len(response.content) > 0


def test_coordenador_gera_relatorio_turmas_professor_pdf(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    setup_matricula_existente: dict,
):
    """
    Testa US-012: Coordenador gera PDF de Turmas por Professor.

    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )

    periodo = setup_matricula_existente["periodo"]

    response = client.get(f"/periodos-letivos/{periodo.id}/relatorio-turmas-professor")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert (
        f"relatorio_turmas_professor_{periodo.ano}_{periodo.semestre}.pdf"
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

    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )

    payload_atualizacao = {
        "ano": 2026,
        "semestre": 1,
        "inicio_matricula": "2026-01-05",
        "fim_matricula": "2026-01-15",
        "fim_trancamento": "2026-03-10",
    }

    response = client.put(f"/periodos-letivos/{periodo.id}", json=payload_atualizacao)

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

    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )

    response = client.delete(f"/periodos-letivos/{id_periodo}")

    assert response.status_code == 204

    periodo_db = db_session.get(model.PeriodoLetivo, id_periodo)
    assert periodo_db is None
