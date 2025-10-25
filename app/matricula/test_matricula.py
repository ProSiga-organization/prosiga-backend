import pytest
from unittest.mock import MagicMock, patch
from app.matricula.repository import MatriculaRepository
from app import model
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import deps
from app.conftest import mock_auth_aluno, mock_auth_professor

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


def test_matricular_aluno_sucesso(client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_turmas: dict):
    """
    Testa US-019: Matrícula de aluno com sucesso (turma com vagas).
   
    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)
    
    id_turma_com_vaga = setup_turmas["turma_com_vaga"].id
    response = client.post(
        "/matriculas/",
        json={"id_turma": id_turma_com_vaga}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["id_aluno"] == mock_aluno.id
    assert data["id_turma"] == id_turma_com_vaga
    assert data["status"] == "EM_CURSO"
    
    matricula_db = db_session.query(model.Matricula).filter_by(
        id_aluno=mock_aluno.id, id_turma=id_turma_com_vaga
    ).first()
    assert matricula_db is not None

def test_matricular_aluno_sem_vagas(client: TestClient, mock_aluno: model.Aluno, setup_turmas: dict):
    """
    Testa US-019: Falha ao matricular em turma lotada.
   
    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)
    id_turma_sem_vaga = setup_turmas["turma_sem_vaga"].id
    
    response = client.post(
        "/matriculas/",
        json={"id_turma": id_turma_sem_vaga}
    )
    
    assert response.status_code == 400
    assert "Não há mais vagas disponíveis" in response.json()["detail"]

def test_matricular_aluno_duplicado(client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_turmas: dict):
    """
    Testa US-019: Falha ao matricular 2x na mesma turma.
   
    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)
    id_turma_com_vaga = setup_turmas["turma_com_vaga"].id

    response_1 = client.post(
        "/matriculas/",
        json={"id_turma": id_turma_com_vaga}
    )
    assert response_1.status_code == 201
    
    response_2 = client.post(
        "/matriculas/",
        json={"id_turma": id_turma_com_vaga}
    )
    
    assert response_2.status_code == 409
    assert "Aluno já matriculado nesta turma" in response_2.json()["detail"]

def test_matricular_como_professor_falha(client: TestClient, mock_professor: model.Professor, setup_turmas: dict):
    """
    Testa US-019: Falha de permissão (Professor não pode se matricular).
   
    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_professor(mock_professor)
    id_turma_com_vaga = setup_turmas["turma_com_vaga"].id
    
    response = client.post(
        "/matriculas/",
        json={"id_turma": id_turma_com_vaga}
    )
    
    assert response.status_code == 403
    assert "Apenas alunos podem se matricular" in response.json()["detail"]