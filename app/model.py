
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum, Date, Float, ForeignKey
)
from sqlalchemy.orm import relationship
from .database import Base
import enum

class StatusContaEnum(str, enum.Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    NOVO = "NOVO"

class StatusAprovacaoEnum(str, enum.Enum):
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"
    TRANCADO = "TRANCADO"


class Usuario(Base):
    __tablename__ = "usuarios"

    id: int = Column(Integer, primary_key=True, index=True)
    cpf: str = Column(String(11), unique=True, nullable=False, index=True)
    nome: str = Column(String(100), nullable=False)
    email: str = Column(String(100), unique=True, nullable=True, index=True)
    senha_hash: str = Column(String(255), nullable=False)
    status: StatusContaEnum = Column(Enum(StatusContaEnum), default=StatusContaEnum.NOVO)
    
    # Coluna para gerir a herança
    tipo_usuario: str = Column(String(50))

    __mapper_args__ = {
        "polymorphic_on": tipo_usuario,
        "polymorphic_identity": "usuario",
    }


class Aluno(Usuario):
    __mapper_args__ = {"polymorphic_identity": "aluno"}
    matricula: str = Column(String(20), unique=True)
    # Relação com a tabela de Matrículas
    matriculas = relationship("Matricula", back_populates="aluno")

class Professor(Usuario):
    __mapper_args__ = {"polymorphic_identity": "professor"}
    # Relação com a tabela de Turmas
    turmas = relationship("Turma", back_populates="professor")

class Coordenador(Usuario):
    __mapper_args__ = {"polymorphic_identity": "coordenador"}


class Curso(Base):
    __tablename__ = "cursos"
    id: int = Column(Integer, primary_key=True, index=True)
    codigo: str = Column(String(20), unique=True, nullable=False)
    nome: str = Column(String(100), nullable=False)

class Disciplina(Base):
    __tablename__ = "disciplinas"
    id: int = Column(Integer, primary_key=True, index=True)
    codigo: str = Column(String(20), unique=True, nullable=False)
    nome: str = Column(String(100), nullable=False)
    eh_obrigatoria: bool = Column(Boolean, default=True)

class PeriodoLetivo(Base):
    __tablename__ = "periodos_letivos"
    id: int = Column(Integer, primary_key=True, index=True)
    ano: int = Column(Integer, nullable=False)
    semestre: int = Column(Integer, nullable=False)
    inicio_matricula: Date = Column(Date)
    fim_matricula: Date = Column(Date)
    fim_trancamento: Date = Column(Date)

class Turma(Base):
    __tablename__ = "turmas"
    id: int = Column(Integer, primary_key=True, index=True)
    codigo: str = Column(String(20), unique=True, nullable=False)
    vagas: int = Column(Integer, nullable=False)
    horario: str = Column(String(100))
    local: str = Column(String(100))
    
    # Chaves Estrangeiras e Relações
    id_disciplina: int = Column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    id_professor: int = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    id_periodo_letivo: int = Column(Integer, ForeignKey("periodos_letivos.id"), nullable=False)

    professor = relationship("Professor", back_populates="turmas")
    matriculas = relationship("Matricula", back_populates="turma")

class Matricula(Base):
    __tablename__ = "matriculas"
    id_aluno: int = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    id_turma: int = Column(Integer, ForeignKey("turmas.id"), primary_key=True)
    nota_final: float = Column(Float)
    status: StatusAprovacaoEnum = Column(Enum(StatusAprovacaoEnum))

    # Relações
    aluno = relationship("Aluno", back_populates="matriculas")
    turma = relationship("Turma", back_populates="matriculas")