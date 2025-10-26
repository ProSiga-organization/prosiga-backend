from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import deps, model
from app.conftest import (mock_auth_aluno, mock_auth_coordenador,
                          mock_auth_professor)
from app.main import app
from app.matricula.repository import MatriculaRepository


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


def test_matricular_aluno_sucesso(
    client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_turmas: dict
):
    """
    Testa US-019: Matrícula de aluno com sucesso (turma com vagas).

    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)

    id_turma_com_vaga = setup_turmas["turma_com_vaga"].id
    response = client.post("/matriculas/", json={"id_turma": id_turma_com_vaga})

    assert response.status_code == 201
    data = response.json()
    assert data["id_aluno"] == mock_aluno.id
    assert data["id_turma"] == id_turma_com_vaga
    assert data["status"] == "EM_CURSO"

    matricula_db = (
        db_session.query(model.Matricula)
        .filter_by(id_aluno=mock_aluno.id, id_turma=id_turma_com_vaga)
        .first()
    )
    assert matricula_db is not None


def test_matricular_aluno_sem_vagas(
    client: TestClient, mock_aluno: model.Aluno, setup_turmas: dict
):
    """
    Testa US-019: Falha ao matricular em turma lotada.

    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)
    id_turma_sem_vaga = setup_turmas["turma_sem_vaga"].id

    response = client.post("/matriculas/", json={"id_turma": id_turma_sem_vaga})

    assert response.status_code == 400
    assert "Não há mais vagas disponíveis" in response.json()["detail"]


def test_matricular_aluno_duplicado(
    client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_turmas: dict
):
    """
    Testa US-019: Falha ao matricular 2x na mesma turma.

    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)
    id_turma_com_vaga = setup_turmas["turma_com_vaga"].id

    response_1 = client.post("/matriculas/", json={"id_turma": id_turma_com_vaga})
    assert response_1.status_code == 201

    response_2 = client.post("/matriculas/", json={"id_turma": id_turma_com_vaga})

    assert response_2.status_code == 409
    assert "Aluno já matriculado nesta turma" in response_2.json()["detail"]


def test_matricular_como_professor_falha(
    client: TestClient, mock_professor: model.Professor, setup_turmas: dict
):
    """
    Testa US-019: Falha de permissão (Professor não pode se matricular).

    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_professor(
        mock_professor
    )
    id_turma_com_vaga = setup_turmas["turma_com_vaga"].id

    response = client.post("/matriculas/", json={"id_turma": id_turma_com_vaga})

    assert response.status_code == 403
    assert "Apenas alunos podem se matricular" in response.json()["detail"]


def test_trancar_disciplina_sucesso_no_prazo(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-024: Trancamento com sucesso, feito DENTRO do prazo.

    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    matricula = setup_matricula_existente["matricula"]

    data_de_hoje_mock = date(2025, 2, 15)

    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(aluno)

    with patch("app.matricula.router.date") as mock_date:
        mock_date.today.return_value = data_de_hoje_mock

        response = client.patch(f"/matriculas/{turma.id}/trancar")

    assert response.status_code == 200
    assert response.json()["status"] == "TRANCADO"

    db_session.refresh(matricula)
    assert matricula.status == model.StatusAprovacaoEnum.TRANCADO


def test_trancar_disciplina_falha_fora_do_prazo(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-024: Falha (400) ao tentar trancar FORA do prazo.

    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    data_de_hoje_mock = date(2025, 3, 2)

    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(aluno)

    with patch("app.matricula.router.date") as mock_date:
        mock_date.today.return_value = data_de_hoje_mock

        response = client.patch(f"/matriculas/{turma.id}/trancar")

    assert response.status_code == 400
    assert "Prazo para trancamento encerrado" in response.json()["detail"]


def test_trancar_disciplina_falha_status_invalido(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-024: Falha (400) ao tentar trancar uma disciplina já trancada.

    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    matricula = setup_matricula_existente["matricula"]

    matricula.status = model.StatusAprovacaoEnum.TRANCADO
    db_session.commit()

    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(aluno)

    data_de_hoje_mock = date(2025, 2, 15)

    with patch("app.matricula.router.date") as mock_date:
        mock_date.today.return_value = data_de_hoje_mock

        response = client.patch(f"/matriculas/{turma.id}/trancar")

    assert response.status_code == 400
    assert "Não é possível trancar. Status atual: TRANCADO" in response.json()["detail"]


def test_aluno_lista_suas_matriculas(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-022: Aluno lista suas próprias matrículas.

    """

    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]

    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(aluno)

    response = client.get("/matriculas/me")

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
    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(mock_aluno)

    response = client.get("/matriculas/me")

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

    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(
        professor
    )

    response = client.get(f"/turmas/{turma.id}/matriculas")

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

    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(aluno)

    response = client.get(f"/turmas/{turma.id}/colegas")

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

    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(mock_aluno)

    response = client.get(f"/turmas/{turma_alheia.id}/colegas")

    assert response.status_code == 403
    assert "Você não está matriculado nesta turma" in response.json()["detail"]


def test_coordenador_matricula_aluno_em_turma_lotada(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    mock_aluno: model.Aluno,
    setup_turmas: dict,
):
    """
    Testa US-011: Coordenador matricula aluno (por matrícula)
    e IGNORA a restrição de vagas (turma_sem_vaga tem 0 vagas).

    """

    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )
    turma_lotada = setup_turmas["turma_sem_vaga"]

    payload = {"matricula_aluno": mock_aluno.matricula, "id_turma": turma_lotada.id}

    response = client.post("/matriculas/admin/matricular", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id_aluno"] == mock_aluno.id
    assert data["id_turma"] == turma_lotada.id


def test_coordenador_matricula_aluno_nao_encontrado(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    setup_turmas: dict,
):
    """
    Testa US-011: Falha (404) se o coordenador tentar matricular
    um aluno com número de matrícula inexistente.

    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(
        mock_coordenador
    )

    id_turma = setup_turmas["turma_com_vaga"].id

    payload = {"matricula_aluno": "MATRICULA-FANTASMA-999", "id_turma": id_turma}

    response = client.post("/matriculas/admin/matricular", json=payload)

    assert response.status_code == 404
    assert "Aluno não encontrado com esta matrícula" in response.json()["detail"]


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

    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(
        professor
    )

    payload = {"nota_final": 8.5, "status": "APROVADO"}

    response = client.patch(f"/matriculas/{turma.id}/{aluno.matricula}", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["nota_final"] == 8.5
    assert data["status"] == "APROVADO"

    db_session.refresh(matricula)
    assert matricula.nota_final == 8.5
    assert matricula.status == model.StatusAprovacaoEnum.APROVADO
