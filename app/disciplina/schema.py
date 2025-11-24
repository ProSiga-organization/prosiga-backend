from pydantic import BaseModel

class DisciplinaResponse(BaseModel):
    id: int
    codigo: str
    nome: str
    semestre_ideal: int | None = None

    class Config:
        from_attributes = True