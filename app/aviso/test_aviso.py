from unittest.mock import MagicMock, patch

import pytest
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


@pytest.mark.parametrize(
    "user_fixture, expected_status, expected_detail",
    [
        ("mock_professor", 201, None),
        (
            "mock_aluno",
            403,
            "Acesso negado: Apenas para professores.",
        ),
        (
            "mock_coordenador",
            403,
            "Acesso negado: Apenas para professores.",
        ),
    ],
)
def test_create_aviso_para_turma_permissoes(
    client: TestClient,
    db_session: Session,
    setup_aviso_context: dict,
    user_fixture: str,
    expected_status: int,
    expected_detail: str | None,
    request,
):
    """
    Testa US-025: Permissões de criação de aviso de turma.
    - Professor (dono) deve criar com sucesso (201).
    - Aluno deve falhar (403).
    - Coordenador deve falhar (403) no endpoint de turma.
    """
    current_user = request.getfixturevalue(user_fixture)
    id_turma = setup_aviso_context["turma"].id

    payload = {
        "titulo": "Aviso Teste",
        "conteudo": "Detalhes...",
        "id_turma": id_turma,
    }

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
        response = client.post(
            "/avisos/turma",
            json=payload,
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == expected_status

    if expected_detail:
        assert expected_detail in response.json()["detail"]
    else:
        data = response.json()
        assert data["titulo"] == "Aviso Teste"
        assert data["autor"]["id"] == current_user.id
        assert data["id_turma"] == id_turma


def test_coordenador_cria_aviso_curso_sucesso(
    client: TestClient,
    db_session: Session,
    setup_aviso_context: dict,
    mock_coordenador: model.Coordenador,
):
    """
    Testa US-026: Coordenador cria aviso para um curso.
    """
    id_curso = setup_aviso_context["curso"].id

    payload = {
        "titulo": "Aviso do Curso",
        "conteudo": "Detalhes...",
        "id_curso": id_curso,
    }

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.post(
            "/avisos/curso",
            json=payload,
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Aviso do Curso"
    assert data["autor"]["id"] == mock_coordenador.id
    assert data["id_curso"] == id_curso


def test_aluno_le_avisos(
    client: TestClient,
    db_session: Session,
    setup_aviso_context: dict,
    mock_professor: model.Professor,
    mock_coordenador: model.Coordenador,
    mock_aluno: model.Aluno,
):
    """
    Testa US-027: Aluno (ou qualquer usuário) lê avisos.
    """
    id_turma = setup_aviso_context["turma"].id
    id_curso = setup_aviso_context["curso"].id

    aviso_turma = model.Aviso(
        titulo="Aviso T1", id_turma=id_turma, id_autor=mock_professor.id
    )
    aviso_curso = model.Aviso(
        titulo="Aviso C1", id_curso=id_curso, id_autor=mock_coordenador.id
    )
    db_session.add_all([aviso_turma, aviso_curso])
    db_session.commit()

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)):
        headers = {"Authorization": "Bearer fake-token"}
        response_turma = client.get(f"/avisos/turma/{id_turma}", headers=headers)
        assert response_turma.status_code == 200
        data_turma = response_turma.json()
        assert len(data_turma) == 1
        assert data_turma[0]["titulo"] == "Aviso T1"

        response_curso = client.get(f"/avisos/curso/{id_curso}", headers=headers)
        assert response_curso.status_code == 200
        data_curso = response_curso.json()
        assert len(data_curso) == 1
        assert data_curso[0]["titulo"] == "Aviso C1"


@pytest.mark.parametrize(
    "user_fixture, http_method, expected_status, expected_detail",
    [
        ("mock_professor", "PUT", 200, None),
        (
            "mock_aluno",
            "PUT",
            403,
            "Acesso negado: Você não é o autor deste aviso",
        ),
        ("mock_professor", "DELETE", 204, None),
        (
            "mock_aluno",
            "DELETE",
            403,
            "Acesso negado: Você não é o autor deste aviso",
        ),
    ],
)
def test_autor_edita_deleta_proprio_aviso(
    client: TestClient,
    db_session: Session,
    mock_professor: model.Professor,
    mock_aluno: model.Aluno,
    user_fixture: str,
    http_method: str,
    expected_status: int,
    expected_detail: str | None,
    request,
):
    """
    Testa US-025/026:
    - Autor (Professor) edita seu próprio aviso (PUT).
    - Autor (Professor) deleta seu próprio aviso (DELETE).
    - Não-autor (Aluno) falha ao editar aviso de outro (PUT 403).
    - Não-autor (Aluno) falha ao deletar aviso de outro (DELETE 403).
    """
    aviso_original = model.Aviso(
        titulo="Titulo Original",
        conteudo="Conteudo Antigo",
        id_autor=mock_professor.id,
    )
    db_session.add(aviso_original)
    db_session.commit()

    current_user = request.getfixturevalue(user_fixture)
    headers = {"Authorization": "Bearer fake-token"}
    url = f"/avisos/{aviso_original.id}"

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
        if http_method == "PUT":
            response = client.put(
                url, json={"titulo": "Titulo Atualizado"}, headers=headers
            )
        elif http_method == "DELETE":
            response = client.delete(url, headers=headers)

    assert response.status_code == expected_status

    if expected_detail:
        assert expected_detail in response.json()["detail"]
    elif http_method == "PUT":
        assert response.json()["titulo"] == "Titulo Atualizado"
    elif http_method == "DELETE":
        aviso_db = db_session.get(model.Aviso, aviso_original.id)
        assert aviso_db is None
