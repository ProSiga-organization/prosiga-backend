import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from . import model
from .database import get_db
from .usuario.repository import UsuarioRepository

# URL do serviço de autenticação externo
AUTH_SERVICE_URL = "http://auth-prosiga:8000/login/me"

# Esquema de segurança para tokens Bearer
security_scheme = HTTPBearer()

# Repositório para operações com usuários
repo = UsuarioRepository()


def get_current_user(
    db: Session = Depends(get_db),
    token: HTTPAuthorizationCredentials = Depends(security_scheme),
) -> model.Usuario:
    """
    Esta dependência valida o token fazendo uma chamada ao serviço de autenticação
    e retorna o objeto completo do usuário a partir do banco de dados local.
    """
    try:
        # Valida o token com o serviço de autenticação
        headers = {"Authorization": f"Bearer {token.credentials}"}
        response = requests.get(AUTH_SERVICE_URL, headers=headers, timeout=5.0)
        response.raise_for_status()

        # Extrai o email do usuário da resposta
        user_data = response.json()
        email = user_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido.")

        user = repo.get_by_email(db, email=email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        return user

    except requests.RequestException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais com o serviço de autenticação.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_aluno(
    current_user: model.Usuario = Depends(get_current_user),
) -> model.Aluno:
    """
    Verifica se o usuário logado é um Aluno. Se não for, lança um erro.
    """
    if not isinstance(current_user, model.Aluno):
        raise HTTPException(
            status_code=403, detail="Acesso negado: Apenas para alunos."
        )
    return current_user


def get_current_professor(
    current_user: model.Usuario = Depends(get_current_user),
) -> model.Professor:
    """
    Verifica se o usuário logado é um Professor.
    """
    if not isinstance(current_user, model.Professor):
        raise HTTPException(
            status_code=403, detail="Acesso negado: Apenas para professores."
        )
    return current_user


def get_current_coordenador(
    current_user: model.Usuario = Depends(get_current_user),
) -> model.Coordenador:
    """
    Verifica se o usuário logado é um Coordenador.
    """
    if not isinstance(current_user, model.Coordenador):
        raise HTTPException(
            status_code=403, detail="Acesso negado: Apenas para coordenadores."
        )
    return current_user
