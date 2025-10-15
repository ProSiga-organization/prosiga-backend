from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from sqlalchemy.orm import Session
from . import model
from .database import get_db
from .usuario.repository import UsuarioRepository

AUTH_SERVICE_URL = "http://auth-prosiga:8000/login/me" 
security_scheme = HTTPBearer()
repo = UsuarioRepository()

def get_current_user(db: Session = Depends(get_db), token: HTTPAuthorizationCredentials = Depends(security_scheme)) -> model.Usuario:
    """
    Esta dependência valida o token fazendo uma chamada ao serviço de autenticação
    e retorna o objeto completo do usuário a partir do banco de dados local.
    """
    try:
        headers = {"Authorization": f"Bearer {token.credentials}"}
        response = requests.get(AUTH_SERVICE_URL, headers=headers)
        response.raise_for_status()

        user_data = response.json()
        email = user_data.get("email")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido.")

        user = repo.get_by_email(db, email=email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        
        return user

    except requests.RequestException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não foi possível validar as credenciais com o serviço de autenticação.",
            headers={"WWW-Authenticate": "Bearer"},
        )