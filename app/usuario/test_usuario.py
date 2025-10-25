import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import model, deps
from app.security import verify_password 
from app.conftest import mock_auth_aluno, mock_auth_coordenador, app
from unittest.mock import patch

def test_primeiro_acesso_sucesso(client: TestClient, db_session: Session):
    """
    Testa o fluxo de US-001: Primeiro acesso com sucesso.
    Um usuário "NOVO" deve conseguir se ativar.
    """
    aluno_novo = model.Aluno(
        cpf="12345678900",
        nome="Aluno Novo Teste",
        matricula="2025-NOVO",
        senha_hash="",
        status=model.StatusContaEnum.NOVO 
    )
    db_session.add(aluno_novo)
    db_session.commit()
    
    payload = {
        "cpf": "12345678900",
        "email": "aluno.novo@teste.com",
        "senha": "NovaSenha@123"
    }
    
    response = client.post("/usuarios/primeiro-acesso", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "aluno.novo@teste.com"
    assert data["status"] == "ATIVO"
    
    db_session.refresh(aluno_novo)
    assert aluno_novo.status == model.StatusContaEnum.ATIVO
    assert aluno_novo.email == "aluno.novo@teste.com"
    assert aluno_novo.senha_hash != ""
    assert verify_password("NovaSenha@123", aluno_novo.senha_hash) is True

def test_primeiro_acesso_cpf_nao_encontrado(client: TestClient):
    """
    Testa o primeiro acesso com um CPF que não existe no banco.
    Deve retornar 404.
    """
    payload = {
        "cpf": "99999999999",
        "email": "fantasma@teste.com",
        "senha": "SenhaInvalida"
    }
    
    response = client.post("/usuarios/primeiro-acesso", json=payload)
    
    assert response.status_code == 404
    assert "CPF não encontrado ou conta já ativa" in response.json()["detail"]

def test_primeiro_acesso_conta_ja_ativa(client: TestClient, mock_aluno: model.Aluno):
    """
    Testa o primeiro acesso para um usuário que já está "ATIVO".
    Deve falhar com 404 (pois o repository não encontra usuário "NOVO").
    """
    payload = {
        "cpf": mock_aluno.cpf,
        "email": "email.novo@teste.com",
        "senha": "NovaSenha"
    }
    
    response = client.post("/usuarios/primeiro-acesso", json=payload)
    
    assert response.status_code == 404
    assert "CPF não encontrado ou conta já ativa" in response.json()["detail"]

def test_upload_csv_sucesso(client: TestClient, db_session: Session, mock_coordenador: model.Coordenador):
    """
    Testa US-005: Upload de CSV de usuários com sucesso.
    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(mock_coordenador)
    
    curso_cc = model.Curso(codigo="CC", nome="Ciencia da Computacao")
    db_session.add(curso_cc)
    db_session.commit()

    csv_content = (
        "cpf,nome,matricula,tipo_usuario,codigo_curso\n"
        "55511122201,Novo Aluno CSV,2025-CSV1,aluno,CC\n"
        "55511122202,Novo Prof CSV,,professor,\n"
    )
    csv_file = io.BytesIO(csv_content.encode('utf-8'))
    csv_file.seek(0)
    response = client.post(
        "/usuarios/upload-csv",
        files={"file": ("usuarios.csv", csv_file, "text/csv")}
    )
    
    assert response.status_code == 201
    assert "2 novos usuários pré-cadastrados com sucesso!" in response.json()["message"]
    
    aluno_db = db_session.query(model.Aluno).filter_by(cpf="55511122201").first()
    prof_db = db_session.query(model.Professor).filter_by(cpf="55511122202").first()
    
    assert aluno_db is not None
    assert aluno_db.nome == "Novo Aluno CSV"
    assert aluno_db.matricula == "2025-CSV1"
    assert aluno_db.status == model.StatusContaEnum.NOVO
    assert aluno_db.id_curso == curso_cc.id
    
    assert prof_db is not None
    assert prof_db.nome == "Novo Prof CSV"
    assert prof_db.status == model.StatusContaEnum.NOVO

def test_upload_csv_erro_curso_invalido(client: TestClient, db_session: Session, mock_coordenador: model.Coordenador):
    """
    Testa US-005: Falha no upload de CSV se o 'codigo_curso' for inválido.
    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(mock_coordenador)
    
    csv_content = "cpf,nome,matricula,tipo_usuario,codigo_curso\n55533344401,Aluno Curso Ruim,2025-CSV2,aluno,INVALIDO\n"
    csv_file = io.BytesIO(csv_content.encode('utf-8'))
    csv_file.seek(0)
    
    response = client.post(
        "/usuarios/upload-csv",
        files={"file": ("usuarios.csv", csv_file, "text/csv")}
    )
    
    assert response.status_code == 400
    assert "Código de curso 'INVALIDO' inválido" in response.json()["detail"]
    
    aluno_db = db_session.query(model.Aluno).filter_by(cpf="55533344401").first()
    assert aluno_db is None

def test_aluno_gera_proprio_historico_pdf(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-021: Aluno gera seu próprio histórico acadêmico em PDF.
   
    """
    aluno = setup_matricula_existente["aluno"]
    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(aluno)

    with patch('app.usuario.router.repo_matricula.get_periodos_cursados_por_aluno', return_value=2) as mock_get_periodos, \
         patch('app.usuario.router.repo_matricula.calcular_ira', return_value=4.2) as mock_calcular_ira:

        response = client.get("/usuarios/me/historico-pdf")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert f"historico_{aluno.matricula}.pdf" in response.headers["content-disposition"]
    assert len(response.content) > 0
    mock_get_periodos.assert_called_once_with(db_session, id_aluno=aluno.id)
    mock_calcular_ira.assert_called_once_with(db_session, id_aluno=aluno.id)