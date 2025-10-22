from pydantic import BaseModel
from typing import List 

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