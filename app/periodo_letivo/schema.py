from pydantic import BaseModel
from datetime import date

class PeriodoLetivoBase(BaseModel):
    ano: int
    semestre: int
    inicio_matricula: date
    fim_matricula: date
    fim_trancamento: date

class PeriodoLetivoCreate(PeriodoLetivoBase):
    pass

# Schema para a resposta da API (inclui o 'id' gerado pelo banco)
class PeriodoLetivoResponse(PeriodoLetivoBase):
    id: int

    class Config:
        from_attributes = True