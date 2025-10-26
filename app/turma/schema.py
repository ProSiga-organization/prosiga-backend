import enum
from typing import List, Optional

from pydantic import BaseModel


class StatusTurmaAluno(str, enum.Enum):
    A_FAZER = "A_FAZER"
    CURSANDO = "CURSANDO"
    JA_CONCLUIDO = "JA_CONCLUIDO"
    TRANCADO = "TRANCADO"


class AvaliacaoTurmaBase(BaseModel):
    nome: str


class AvaliacaoTurmaCreate(AvaliacaoTurmaBase):
    pass


class AvaliacaoTurmaResponse(AvaliacaoTurmaBase):
    id: int
    id_turma: int

    class Config:
        from_attributes = True


class TurmaBase(BaseModel):
    codigo: str
    vagas: int
    horario: str | None = None
    local: str | None = None
    id_disciplina: int
    id_professor: int
    id_periodo_letivo: int


class TurmaCreate(TurmaBase):
    pass


class TurmaResponse(TurmaBase):
    id: int
    avaliacoes_definidas: List[AvaliacaoTurmaResponse] = []

    class Config:
        from_attributes = True


class TurmaBuscaAlunoResponse(BaseModel):
    id_turma: int
    codigo_turma: str
    vagas_disponiveis: int
    horario: Optional[str] = None
    local: Optional[str] = None
    codigo_disciplina: str
    nome_disciplina: str
    descricao: Optional[str] = None
    semestre_ideal: Optional[int] = None
    status_aluno: StatusTurmaAluno
