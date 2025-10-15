from pydantic import BaseModel
from ..model import StatusAprovacaoEnum

class MatriculaCreate(BaseModel):
    id_turma: int

class MatriculaResponse(BaseModel):
    id_aluno: int
    id_turma: int
    status: StatusAprovacaoEnum | None = None
    nota_final: float | None = None

    class Config:
        from_attributes = True