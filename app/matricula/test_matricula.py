from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import model
from app.matricula.repository import MatriculaRepository

AUTH_MOCK_PATH = "app.deps.requests.get"


def mock_auth_response(user_model):
    """Cria um mock de resposta bem-sucedida do serviço de autenticação."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"email": user_model.email, "id": user_model.id}
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_calcular_ira_sem_disciplinas():
    """
    Testa US-101: Cálculo de IRA para aluno sem histórico.
    O IRA deve ser 5.0 (o valor inicial).
    """
    mock_db = MagicMock()

    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = []
    mock_db.query.return_value = mock_query

    repo = MatriculaRepository()
    id_aluno_teste = 1

    ira = repo.calcular_ira(db=mock_db, id_aluno=id_aluno_teste)

    assert ira == 5.0


def test_calcular_ira_com_historico():
    """
    Testa US-101: Cálculo de IRA com notas.
    IRA = (Média das notas 0-10) / 2
    """
    mock_db = MagicMock()

    m1 = MagicMock(spec=model.Matricula)
    m1.nota_final = 10.0
    m1.status = model.StatusAprovacaoEnum.APROVADO

    m2 = MagicMock(spec=model.Matricula)
    m2.nota_final = 5.0
    m2.status = model.StatusAprovacaoEnum.REPROVADO

    m3 = MagicMock(spec=model.Matricula)
    m3.nota_final = 8.0
    m3.status = model.StatusAprovacaoEnum.APROVADO

    m4_em_curso = MagicMock(spec=model.Matricula)
    m4_em_curso.nota_final = None
    m4_em_curso.status = model.StatusAprovacaoEnum.EM_CURSO

    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [m1, m2, m3]
    mock_db.query.return_value = mock_query

    repo = MatriculaRepository()
    id_aluno_teste = 1
    ira = repo.calcular_ira(db=mock_db, id_aluno=id_aluno_teste)
    assert ira == 3.83


@pytest.mark.parametrize(
    "user_fixture, turma_key, expected_status, expected_detail",
    [
        ("mock_aluno", "turma_com_vaga", 201, None),
        ("mock_aluno", "turma_sem_vaga", 400, "Não há mais vagas disponíveis"),
        (
            "mock_professor",
            "turma_com_vaga",
            403,
            "Apenas alunos podem se matricular",
        ),
        (
            "mock_coordenador",
            "turma_com_vaga",
            403,
            "Apenas alunos podem se matricular",
        ),
    ],
)
def test_create_matricula_permissoes_e_vagas(
    client: TestClient,
    setup_turmas: dict,
    user_fixture: str,
    turma_key: str,
    expected_status: int,
    expected_detail: str | None,
    request,
):
    """
    Testa US-019: Matrícula de aluno com sucesso (turma com vagas).
    Testa US-019: Falha ao matricular em turma lotada.
    Testa US-019: Falha de permissão (Professor/Coordenador não pode se matricular).
    """
    current_user = request.getfixturevalue(user_fixture)
    id_turma = setup_turmas[turma_key].id
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
        response = client.post(
            "/matriculas/", json={"id_turma": id_turma}, headers=headers
        )

    assert response.status_code == expected_status

    if expected_detail:
        assert expected_detail in response.json()["detail"]
    else:
        data = response.json()
        assert data["id_aluno"] == current_user.id
        assert data["id_turma"] == id_turma
        assert data["status"] == "EM_CURSO"


def test_matricular_aluno_duplicado(
    client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_turmas: dict
):
    """
    Testa US-019: Falha ao matricular 2x na mesma turma.
    """
    id_turma_com_vaga = setup_turmas["turma_com_vaga"].id
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)):
        response_1 = client.post(
            "/matriculas/", json={"id_turma": id_turma_com_vaga}, headers=headers
        )
        assert response_1.status_code == 201

        response_2 = client.post(
            "/matriculas/", json={"id_turma": id_turma_com_vaga}, headers=headers
        )

    assert response_2.status_code == 409
    assert "Aluno já matriculado nesta turma" in response_2.json()["detail"]


@pytest.mark.parametrize(
    "data_hoje, status_inicial, expected_status_code, expected_detail_or_status",
    [
        (date(2025, 2, 15), model.StatusAprovacaoEnum.EM_CURSO, 200, "TRANCADO"),
        (
            date(2025, 3, 2),
            model.StatusAprovacaoEnum.EM_CURSO,
            400,
            "Prazo para trancamento encerrado",
        ),
        (
            date(2025, 2, 15),
            model.StatusAprovacaoEnum.TRANCADO,
            400,
            "Não é possível trancar. Status atual: TRANCADO",
        ),
        (
            date(2025, 2, 15),
            model.StatusAprovacaoEnum.APROVADO,
            400,
            "Não é possível trancar. Status atual: APROVADO",
        ),
    ],
)
def test_trancar_disciplina_cenarios(
    client: TestClient,
    db_session: Session,
    setup_matricula_existente: dict,
    data_hoje: date,
    status_inicial: model.StatusAprovacaoEnum,
    expected_status_code: int,
    expected_detail_or_status: str,
):
    """
    Testa US-024: Vários cenários de trancamento de disciplina.
    - Sucesso (Dentro do prazo, status EM_CURSO).
    - Falha (Fora do prazo).
    - Falha (Status inválido, ex: já TRANCADO).
    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    matricula = setup_matricula_existente["matricula"]

    matricula.status = status_inicial
    db_session.commit()

    with patch(
        AUTH_MOCK_PATH, return_value=mock_auth_response(aluno)
    ) as mock_auth, patch("app.matricula.router.date") as mock_date:
        mock_date.today.return_value = data_hoje
        headers = {"Authorization": "Bearer fake-token"}
        response = client.patch(f"/matriculas/{turma.id}/trancar", headers=headers)

    assert response.status_code == expected_status_code

    if expected_status_code == 200:
        assert response.json()["status"] == expected_detail_or_status
        db_session.refresh(matricula)
        assert matricula.status == model.StatusAprovacaoEnum.TRANCADO
    else:
        assert expected_detail_or_status in response.json()["detail"]


def test_aluno_lista_suas_matriculas(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-022: Aluno lista suas próprias matrículas.
    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(aluno)):
        response = client.get(
            "/matriculas/me", headers={"Authorization": "Bearer fake-token"}
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id_aluno"] == aluno.id
    assert data[0]["id_turma"] == turma.id


def test_aluno_sem_matriculas_lista_vazio(
    client: TestClient, db_session: Session, mock_aluno: model.Aluno
):
    """
    Testa US-022: Aluno sem matrículas recebe 404.
    (Nota: O endpoint levanta 404 se a lista for vazia)
    """
    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)):
        response = client.get(
            "/matriculas/me", headers={"Authorization": "Bearer fake-token"}
        )

    assert response.status_code == 404
    assert "Nenhuma matrícula encontrada" in response.json()["detail"]


def test_professor_lista_alunos_da_turma(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-015: Professor (dono) lista alunos/matrículas da sua turma.
    """
    professor = setup_matricula_existente["professor"]
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(professor)):
        response = client.get(
            f"/turmas/{turma.id}/matriculas",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id_aluno"] == aluno.id
    assert data[0]["id_turma"] == turma.id


def test_aluno_lista_colegas_de_turma(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-023: Aluno (matriculado) lista seus colegas.
    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(aluno)):
        response = client.get(
            f"/turmas/{turma.id}/colegas",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["nome"] == aluno.nome
    assert data[0]["matricula"] == aluno.matricula


def test_aluno_nao_lista_colegas_se_nao_matriculado(
    client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_turmas: dict
):
    """
    Testa US-023: Falha (403) se o aluno tentar ver colegas de uma
    turma onde ele NÃO está matriculado.
    """
    turma_alheia = setup_turmas["turma_com_vaga"]

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)):
        response = client.get(
            f"/turmas/{turma_alheia.id}/colegas",
            headers={"Authorization": "Bearer fake-token"},
        )

    assert response.status_code == 403
    assert "Você não está matriculado nesta turma" in response.json()["detail"]


@pytest.mark.parametrize(
    "matricula_aluno, id_turma_key, expected_status, expected_detail",
    [
        ("2025-TESTE", "turma_sem_vaga", 201, None),
        ("MATRICULA-FANTASMA-999", "turma_com_vaga", 404, "Aluno não encontrado"),
        ("2025-TESTE", "turma_com_vaga", 409, "Aluno já matriculado"),
    ],
)
def test_coordenador_admin_create_matricula(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    mock_aluno: model.Aluno,
    setup_turmas: dict,
    matricula_aluno: str,
    id_turma_key: str,
    expected_status: int,
    expected_detail: str | None,
):
    """
    Testa US-011: Coordenador matricula aluno (por matrícula)
    - Sucesso (ignorando vagas).
    - Falha (Aluno não encontrado).
    - Falha (Matrícula duplicada).
    """
    if expected_status == 409:
        matricula_existente = model.Matricula(
            id_aluno=mock_aluno.id, id_turma=setup_turmas["turma_com_vaga"].id
        )
        db_session.add(matricula_existente)
        db_session.commit()

    turma = setup_turmas[id_turma_key]
    payload = {"matricula_aluno": matricula_aluno, "id_turma": turma.id}
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.post(
            "/matriculas/admin/matricular", json=payload, headers=headers
        )

    assert response.status_code == expected_status
    if expected_detail:
        assert expected_detail in response.json()["detail"]
    else:
        assert response.json()["id_aluno"] == mock_aluno.id


def test_professor_atualiza_nota_final_e_status_aluno(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-015: Professor (dono) atualiza a nota final e o status
    (APROVADO/REPROVADO) de um aluno.
    """
    professor = setup_matricula_existente["professor"]
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    matricula = setup_matricula_existente["matricula"]

    payload = {"nota_final": 8.5, "status": "APROVADO"}
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(professor)):
        response = client.patch(
            f"/matriculas/{turma.id}/{aluno.matricula}", json=payload, headers=headers
        )

    assert response.status_code == 200
    data = response.json()
    assert data["nota_final"] == 8.5
    assert data["status"] == "APROVADO"

    db_session.refresh(matricula)
    assert matricula.nota_final == 8.5
    assert matricula.status == model.StatusAprovacaoEnum.APROVADO
