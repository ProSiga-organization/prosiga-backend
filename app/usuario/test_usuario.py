import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import model
from app.security import verify_password 

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
    #
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