import enum
from typing import List, Optional

from pydantic import BaseModel

# Schemas para sistema de turmas e avaliações

class StatusTurmaAluno(str, enum.Enum):
    """Status da relação do aluno com a turma"""
    A_FAZER = "A_FAZER"
    CURSANDO = "CURSANDO"
    JA_CONCLUIDO = "JA_CONCLUIDO"
    TRANCADO = "TRANCADO"


class AvaliacaoTurmaBase(BaseModel):
    """Campos básicos para avaliações de turma"""
    nome: str


class AvaliacaoTurmaCreate(AvaliacaoTurmaBase):
    pass


class AvaliacaoTurmaResponse(AvaliacaoTurmaBase):
    id: int
    id_turma: int

    class Config:
        from_attributes = True


class TurmaBase(BaseModel):
    """Campos básicos para turmas"""
    codigo: str
    vagas: int
    horario: str | None = None
    local: str | None = None
    id_disciplina: int
    id_professor: int
    id_periodo_letivo: int


class TurmaCreate(TurmaBase):
    """Schema para criação de turmas"""
    pass


class TurmaResponse(TurmaBase):
    """Schema de resposta completo para turma"""
    id: int
    avaliacoes_definidas: List[AvaliacaoTurmaResponse] = []  # Lista de avaliações

    class Config:
        from_attributes = True


class TurmaBuscaAlunoResponse(BaseModel):
    """Schema otimizado para busca de turmas pelos alunos"""
    id_turma: int
    codigo_turma: str
    vagas_disponiveis: int
    horario: Optional[str] = None
    local: Optional[str] = None
    codigo_disciplina: str
    nome_disciplina: str
    descricao: Optional[str] = None
    semestre_ideal: Optional[int] = None
    status_aluno: StatusTurmaAluno  # Status do aluno em relação à turma
