from typing import Optional, Union

from pydantic import BaseModel, EmailStr

from app.model import StatusContaEnum

# Schemas para sistema de usuários


class PrimeiroAcessoSchema(BaseModel):
    """Schema para ativação de conta no primeiro acesso"""

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
    id_curso: Optional[int] = None

    class Config:
        model_config = {"from_attributes": True}


class AlunoResponse(UsuarioBaseResponse):
    """Schema de resposta específico para alunos"""

    matricula: str


class ProfessorResponse(UsuarioBaseResponse):
    """Schema de resposta específico para professores"""

    pass


class CoordenadorResponse(UsuarioBaseResponse):
    """Schema de resposta específico para coordenadores"""

    pass


# União de todos os tipos de usuário para respostas polimórficas
AnyUsuarioResponse = Union[AlunoResponse, ProfessorResponse, CoordenadorResponse]


class ColegaResponse(BaseModel):
    """Schema para exibir informações públicas de um aluno em uma turma."""

    nome: str
    matricula: str

    class Config:
        model_config = {"from_attributes": True}


class SemestreAtualResponse(BaseModel):
    semestre_atual: int


class IraResponse(BaseModel):
    ira: Optional[float] = None
