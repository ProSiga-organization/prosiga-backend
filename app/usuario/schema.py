from pydantic import BaseModel, EmailStr
from ..model import StatusContaEnum


class PrimeiroAcessoSchema(BaseModel):
    cpf: str
    email: str
    senha: str

class UsuarioResponse(BaseModel):
    id: int
    cpf: str
    nome: str
    email: EmailStr
    status: StatusContaEnum

    class Config:
        model_config = {'from_attributes': True}

class AlunoResponse(UsuarioResponse):
    matricula: str