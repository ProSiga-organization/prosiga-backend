from pydantic import BaseModel
from ..model import StatusAprovacaoEnum
from typing import List, Optional


class NotaAvaliacaoBase(BaseModel):
    nota: Optional[float] = None


class NotaAvaliacaoResponse(NotaAvaliacaoBase):
    id: int
    id_avaliacao_turma: int
    id_matricula_aluno: int

    class Config:
        from_attributes = True


class NotaAvaliacaoCreateUpdate(NotaAvaliacaoBase):
    """Schema para o professor lançar/atualizar a nota de um aluno em uma avaliação"""

    matricula_aluno: str
    id_avaliacao_turma: int


class MatriculaCreate(BaseModel):
    id_turma: int


class MatriculaUpdate(BaseModel):
    """Schema para atualizar apenas nota final e status da matrícula"""

    nota_final: Optional[float] = None
    status: Optional[StatusAprovacaoEnum] = None


class MatriculaResponse(BaseModel):
    id_aluno: int
    id_turma: int
    status: Optional[StatusAprovacaoEnum] = None
    nota_final: Optional[float] = None

    notas_avaliacoes: List[NotaAvaliacaoResponse] = []

    class Config:
        from_attributes = True


class AdminMatriculaCreate(BaseModel):
    """Schema para o admin matricular um aluno manualmente."""

    matricula_aluno: str
    id_turma: int
