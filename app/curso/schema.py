from pydantic import BaseModel

class CursoBase(BaseModel):
    codigo: str
    nome: str

class CursoResponse(CursoBase):
    id: int

    class Config:
        from_attributes = True