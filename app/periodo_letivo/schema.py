from datetime import date

from pydantic import BaseModel

# Schemas para sistema de períodos letivos

class PeriodoLetivoBase(BaseModel):
    """Campos básicos para períodos letivos"""
    ano: int
    semestre: int
    inicio_matricula: date
    fim_matricula: date
    fim_trancamento: date


class PeriodoLetivoCreate(PeriodoLetivoBase):
    """Schema para criação de períodos letivos"""
    pass


# Schema para a resposta da API (inclui o 'id' gerado pelo banco)
class PeriodoLetivoResponse(PeriodoLetivoBase):
    id: int

    class Config:
        from_attributes = True
