import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import deps
from app import model
from app.conftest import mock_auth_professor, mock_auth_aluno, mock_auth_coordenador

def test_professor_cria_avaliacao_coluna(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-015: Professor (dono) cria a "coluna" de avaliação.
    Verifica se a "célula" (NotaAvaliacao) é criada para o aluno existente.
   
    """
    professor = setup_matricula_existente["professor"]
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(professor)
    
    response = client.post(
        f"/turmas/{turma.id}/avaliacoes",
        json={"nome": "P1"}
    )
    
    assert response.status_code == 201
    data_avaliacao = response.json()
    assert data_avaliacao["nome"] == "P1"
    assert data_avaliacao["id_turma"] == turma.id
    id_avaliacao_criada = data_avaliacao["id"]
    
    celula_nota = db_session.query(model.NotaAvaliacao).filter_by(
        id_avaliacao_turma=id_avaliacao_criada,
        id_matricula_aluno=aluno.id
    ).first()
    
    assert celula_nota is not None
    assert celula_nota.nota is None

def test_professor_nao_cria_avaliacao_turma_alheia(client: TestClient, db_session: Session, setup_matricula_existente: dict, mock_coordenador: model.Coordenador):
    """
    Testa US-015: Falha (403) ao tentar criar avaliação em turma de outro professor.
    """
    turma = setup_matricula_existente["turma"] 
    
    outro_professor = model.Professor(
        id=99, cpf="99988877766", nome="Outro Professor", email="outro@prof.com", 
        senha_hash="hash", status=model.StatusContaEnum.ATIVO
    )
    db_session.add(outro_professor)
    db_session.commit()
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(outro_professor)
    response = client.post(
        f"/turmas/{turma.id}/avaliacoes",
        json={"nome": "P-Intrusa"}
    )
    
    assert response.status_code == 403
    assert "Professor não tem permissão para criar avaliações" in response.json()["detail"]

def test_professor_lanca_nota_celula(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-015: Professor lança a nota (atualiza a "célula").
   
    """
    professor = setup_matricula_existente["professor"]
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(professor)
    avaliacao_p1 = model.AvaliacaoTurma(nome="P1", id_turma=turma.id)
    db_session.add(avaliacao_p1)
    db_session.commit()
    
    celula_nota = model.NotaAvaliacao(
        id_avaliacao_turma=avaliacao_p1.id,
        id_matricula_aluno=aluno.id,
        id_matricula_turma=turma.id,
        nota=None
    )
    db_session.add(celula_nota)
    db_session.commit()
    
    id_celula_antes = celula_nota.id

    payload = {
        "matricula_aluno": aluno.matricula, 
        "id_avaliacao_turma": avaliacao_p1.id, 
        "nota": 8.5
    }
    response = client.put("/matriculas/notas", json=payload)
    
    assert response.status_code == 200
    data_nota = response.json()
    assert data_nota["nota"] == 8.5
    assert data_nota["id"] == id_celula_antes 
    
    db_session.refresh(celula_nota)
    assert celula_nota.nota == 8.5

def test_aluno_nao_lanca_propria_nota(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-015: Falha (403) se o Aluno tentar lançar a própria nota.
    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(aluno)
    
    avaliacao_p1 = model.AvaliacaoTurma(nome="P1", id_turma=turma.id)
    db_session.add(avaliacao_p1)
    db_session.commit()

    payload = {
        "matricula_aluno": aluno.matricula,
        "id_avaliacao_turma": avaliacao_p1.id,
        "nota": 10.0 
    }
    response = client.put("/matriculas/notas", json=payload)
    
    assert response.status_code == 403
    assert "Acesso negado: Apenas para professores" in response.json()["detail"]