from pydantic import BaseModel, EmailStr
from ..model import StatusContaEnum
from typing import Union

class PrimeiroAcessoSchema(BaseModel):
    cpf: str
    email: str
    senha: str

class UsuarioBaseResponse(BaseModel):
    """Dados comuns a todos os usuários"""
    id: int
    cpf: str
    nome: str
    email: EmailStr
    status: StatusContaEnum
    tipo_usuario: str

    class Config:
        model_config = {'from_attributes': True}


class AlunoResponse(UsuarioBaseResponse):
    matricula: str

class ProfessorResponse(UsuarioBaseResponse):
    pass

class CoordenadorResponse(UsuarioBaseResponse):
    pass

AnyUsuarioResponse = Union[AlunoResponse, ProfessorResponse, CoordenadorResponse]

class ColegaResponse(BaseModel):
    """Schema para exibir informações públicas de um aluno em uma turma."""
    nome: str
    matricula: str

    class Config:
        model_config = {'from_attributes': True}