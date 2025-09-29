
from pydantic import BaseModel

class TurmaBase(BaseModel):
    descricao: str
    vagas: int
    criterio_aprovacao: str | None = None
    id_professor: int
    id_periodo_letivo: int
    id_disciplina: int

class TurmaRequest(TurmaBase):
    # Para a criação, os campos da classe base são suficientes.
    pass

class TurmaResponse(TurmaBase):
    # Na resposta, incluímos o ID gerado pelo banco.
    id: int

    class Config:
        orm_mode = True