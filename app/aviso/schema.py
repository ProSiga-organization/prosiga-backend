from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AvisoBase(BaseModel):
    """Campos básicos compartilhados por todos os avisos"""

    titulo: str
    conteudo: Optional[str] = None


class AvisoTurmaCreate(AvisoBase):
    """Schema para um Professor criar um aviso para uma turma"""

    id_turma: int


class AvisoCursoCreate(AvisoBase):
    """Schema para um Coordenador criar um aviso para um curso"""

    id_curso: int


class AvisoUpdate(BaseModel):
    """Schema para atualizar o título ou conteúdo de um aviso"""

    titulo: Optional[str] = None
    conteudo: Optional[str] = None


class AutorAvisoResponse(BaseModel):
    """Schema simples para mostrar quem publicou o aviso"""

    id: int
    nome: str

    class Config:
        from_attributes = True


class AvisoResponse(AvisoBase):
    """Schema de resposta completo para um aviso"""

    id: int
    data_publicacao: datetime
    autor: AutorAvisoResponse
    id_turma: Optional[int] = None
    id_curso: Optional[int] = None

    class Config:
        from_attributes = True
