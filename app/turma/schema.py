from pydantic import BaseModel

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

    class Config:
        from_attributes = True