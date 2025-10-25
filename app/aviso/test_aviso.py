import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import deps
from app import model

from app.conftest import (
    mock_auth_aluno, 
    mock_auth_professor, 
    mock_auth_coordenador
)

def test_professor_cria_aviso_turma_sucesso(client: TestClient, db_session: Session, setup_aviso_context: dict, mock_professor: model.Professor):
    """
    Testa US-025: Professor (dono) cria aviso para sua turma.
   
    """
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(mock_professor)
    id_turma = setup_aviso_context["turma"].id
    
    response = client.post(
        "/avisos/turma",
        json={"titulo": "Aviso da Turma", "conteudo": "Detalhes...", "id_turma": id_turma}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Aviso da Turma"
    assert data["autor"]["id"] == mock_professor.id
    assert data["id_turma"] == id_turma
    assert data["id_curso"] is None

def test_coordenador_cria_aviso_curso_sucesso(client: TestClient, db_session: Session, setup_aviso_context: dict, mock_coordenador: model.Coordenador):
    """
    Testa US-026: Coordenador cria aviso para um curso.
   
    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(mock_coordenador)
    id_curso = setup_aviso_context["curso"].id
    
    response = client.post(
        "/avisos/curso",
        json={"titulo": "Aviso do Curso", "conteudo": "Detalhes...", "id_curso": id_curso}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["titulo"] == "Aviso do Curso"
    assert data["autor"]["id"] == mock_coordenador.id
    assert data["id_curso"] == id_curso
    assert data["id_turma"] is None

def test_aluno_le_avisos(client: TestClient, db_session: Session, setup_aviso_context: dict, mock_professor: model.Professor, mock_coordenador: model.Coordenador, mock_aluno: model.Aluno):
    """
    Testa US-027: Aluno (ou qualquer usuário) lê avisos.
   
    """
    id_turma = setup_aviso_context["turma"].id
    id_curso = setup_aviso_context["curso"].id
    
    aviso_turma = model.Aviso(titulo="Aviso T1", id_turma=id_turma, id_autor=mock_professor.id)
    aviso_curso = model.Aviso(titulo="Aviso C1", id_curso=id_curso, id_autor=mock_coordenador.id)
    db_session.add_all([aviso_turma, aviso_curso])
    db_session.commit()
    
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)

    response_turma = client.get(f"/avisos/turma/{id_turma}")
    assert response_turma.status_code == 200
    data_turma = response_turma.json()
    assert len(data_turma) == 1
    assert data_turma[0]["titulo"] == "Aviso T1"
    response_curso = client.get(f"/avisos/curso/{id_curso}")

    assert response_curso.status_code == 200
    data_curso = response_curso.json()
    assert len(data_curso) == 1
    assert data_curso[0]["titulo"] == "Aviso C1"

def test_autor_edita_proprio_aviso(client: TestClient, db_session: Session, mock_professor: model.Professor):
    """
    Testa US-025/026: Autor (Professor) edita seu próprio aviso.
   
    """
    aviso_original = model.Aviso(
        titulo="Titulo Original", 
        conteudo="Conteudo Antigo", 
        id_autor=mock_professor.id
    )
    db_session.add(aviso_original)
    db_session.commit()

    app.dependency_overrides[deps.get_current_user] = mock_auth_professor(mock_professor)

    response = client.put(
        f"/avisos/{aviso_original.id}",
        json={"titulo": "Titulo Atualizado"}
    )
    
    assert response.status_code == 200
    assert response.json()["titulo"] == "Titulo Atualizado"
    assert response.json()["conteudo"] == "Conteudo Antigo"

def test_nao_autor_falha_deletar_aviso(client: TestClient, db_session: Session, mock_professor: model.Professor, mock_aluno: model.Aluno):
    """
    Testa US-025/026: Falha (403) ao tentar deletar aviso de outro.
   
    """
    aviso_do_prof = model.Aviso(
        titulo="Aviso do Prof", 
        id_autor=mock_professor.id
    )
    db_session.add(aviso_do_prof)
    db_session.commit()

    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)

    response = client.delete(f"/avisos/{aviso_do_prof.id}")

    assert response.status_code == 403
    assert "Acesso negado: Você não é o autor deste aviso" in response.json()["detail"]

def test_aluno_falha_criar_aviso_turma(client: TestClient, setup_aviso_context: dict, mock_aluno: model.Aluno):
    """
    Testa US-025: Falha (403) se Aluno tentar criar aviso.
   
    """
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(mock_aluno)
    id_turma = setup_aviso_context["turma"].id
    
    response = client.post(
        "/avisos/turma",
        json={"titulo": "Aviso do Aluno", "id_turma": id_turma}
    )
    
    assert response.status_code == 403
    assert "Acesso negado: Apenas para professores" in response.json()["detail"]