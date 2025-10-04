# app/usuario/schema.py

from pydantic import BaseModel, EmailStr
from ..model import StatusContaEnum

# --- Esquema para o Primeiro Acesso ---
# O usuário precisa de fornecer estes dados para ativar a conta
class PrimeiroAcessoSchema(BaseModel):
    cpf: str
    email: str
    senha: str

# --- Esquemas de Resposta (o que a API retorna) ---
# Usaremos estes para mostrar os dados do usuário após a ativação

class UsuarioResponse(BaseModel):
    id: int
    cpf: str
    nome: str
    email: EmailStr
    status: StatusContaEnum

    class Config:
        orm_mode = True

class AlunoResponse(UsuarioResponse):
    matricula: str