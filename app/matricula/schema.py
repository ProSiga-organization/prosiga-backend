from typing import List, Optional

from pydantic import BaseModel

from ..model import StatusAprovacaoEnum

# Schemas para sistema de matrículas e notas

class NotaAvaliacaoBase(BaseModel):
    """Campos básicos para notas de avaliação"""
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
    """Schema para aluno se matricular em uma turma"""
    id_turma: int


class MatriculaUpdate(BaseModel):
    """Schema para atualizar apenas nota final e status da matrícula"""

    nota_final: Optional[float] = None
    status: Optional[StatusAprovacaoEnum] = None


class MatriculaResponse(BaseModel):
    """Schema de resposta completo para uma matrícula"""
    id_aluno: int
    id_turma: int
    status: Optional[StatusAprovacaoEnum] = None
    nota_final: Optional[float] = None

    notas_avaliacoes: List[NotaAvaliacaoResponse] = []  # Lista de notas nas avaliações

    class Config:
        from_attributes = True


class AdminMatriculaCreate(BaseModel):
    """Schema para o admin matricular um aluno manualmente."""

    matricula_aluno: str
    id_turma: int
