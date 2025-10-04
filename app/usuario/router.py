# app/usuario/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schema 
from ..database import get_db 
from .repository import UsuarioRepository

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

repo = UsuarioRepository()

@router.post("/primeiro-acesso/aluno", 
             response_model=schema.AlunoResponse,
             summary="Realiza o primeiro acesso de um aluno")
def primeiro_acesso_aluno(dados_ativacao: schema.PrimeiroAcessoSchema, db: Session = Depends(get_db)):
    """
    Endpoint para um aluno ativar a sua conta.
    O sistema verifica se o CPF do aluno existe e se a conta está pendente de ativação (status='NOVO').
    Se sim, atualiza os dados com a senha e email fornecidos e ativa a conta.
    """
    # 1. Procura por um aluno pré-cadastrado com o CPF e status 'NOVO'
    aluno_db = repo.get_aluno_para_ativacao(db, cpf=dados_ativacao.cpf)
    
    # 2. Se não encontrar, retorna um erro 404
    if not aluno_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CPF não encontrado ou conta já ativa. Verifique os dados ou contacte a administração."
        )

    # 4. Se encontrou, ativa a conta com os novos dados
    aluno_ativado = repo.ativar_conta_aluno(db, aluno_db=aluno_db, dados_ativacao=dados_ativacao)
    
    return aluno_ativado