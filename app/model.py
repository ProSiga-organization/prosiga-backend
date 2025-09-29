# app/model.py

from sqlalchemy import Column, Integer, String, ForeignKey
from .database import Base

class Turmas(Base):
    __tablename__ = "turmas"

    id: int = Column(Integer, primary_key=True, index=True)
    descricao: str = Column(String(150), nullable=False)
    vagas: int = Column(Integer, nullable=False)
    criterio_aprovacao: str = Column(String(100), nullable=True)

    # Chaves Estrangeiras - estabelecendo os relacionamentos
    id_professor: int = Column(Integer, ForeignKey("professores.id"))
    id_periodo_letivo: int = Column(Integer, ForeignKey("periodos_letivos.id"))
    id_disciplina: int = Column(Integer, ForeignKey("disciplinas.id"))