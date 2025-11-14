import enum

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class StatusContaEnum(str, enum.Enum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    NOVO = "NOVO"


class StatusAprovacaoEnum(str, enum.Enum):
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"
    TRANCADO = "TRANCADO"
    EM_CURSO = "EM_CURSO"


class Usuario(Base):
    __tablename__ = "usuarios"
    id: int = Column(Integer, primary_key=True, index=True)
    cpf: str = Column(String(11), unique=True, nullable=False, index=True)
    nome: str = Column(String(100), nullable=False)
    email: str = Column(String(100), unique=True, nullable=True, index=True)
    senha_hash: str = Column(String(255), nullable=False)
    status: StatusContaEnum = Column(
        Enum(StatusContaEnum), default=StatusContaEnum.NOVO
    )
    tipo_usuario: str = Column(String(50))
    __mapper_args__ = {
        "polymorphic_on": tipo_usuario,
        "polymorphic_identity": "usuario",
    }
    avisos_publicados = relationship("Aviso", back_populates="autor")


class Aluno(Usuario):
    __mapper_args__ = {"polymorphic_identity": "aluno"}
    matricula: str = Column(String(20), unique=True)
    matriculas = relationship("Matricula", back_populates="aluno")
    id_curso: int = Column(Integer, ForeignKey("cursos.id"), nullable=True)
    curso = relationship("Curso", back_populates="alunos")


class Professor(Usuario):
    __mapper_args__ = {"polymorphic_identity": "professor"}
    turmas = relationship("Turma", back_populates="professor")


class Coordenador(Usuario):
    __mapper_args__ = {"polymorphic_identity": "coordenador"}


class Curso(Base):
    __tablename__ = "cursos"
    id: int = Column(Integer, primary_key=True, index=True)
    codigo: str = Column(String(20), unique=True, nullable=False)
    nome: str = Column(String(100), nullable=False)
    avisos = relationship("Aviso", back_populates="curso")
    alunos = relationship("Aluno", back_populates="curso")


class Disciplina(Base):
    __tablename__ = "disciplinas"
    id: int = Column(Integer, primary_key=True, index=True)
    codigo: str = Column(String(20), unique=True, nullable=False)
    nome: str = Column(String(100), nullable=False)
    descricao: str = Column(Text, nullable=True)
    semestre_ideal: int = Column(Integer, nullable=True)


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
    id_disciplina: int = Column(Integer, ForeignKey("disciplinas.id"), nullable=False)
    id_professor: int = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    id_periodo_letivo: int = Column(
        Integer, ForeignKey("periodos_letivos.id"), nullable=False
    )
    professor = relationship("Professor", back_populates="turmas")
    matriculas = relationship(
        "Matricula", back_populates="turma", cascade="all, delete-orphan"
    )
    avaliacoes_definidas = relationship(
        "AvaliacaoTurma", back_populates="turma", cascade="all, delete-orphan"
    )
    avisos = relationship("Aviso", back_populates="turma")
    disciplina = relationship("Disciplina")


class Matricula(Base):
    __tablename__ = "matriculas"
    id_aluno: int = Column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    id_turma: int = Column(Integer, ForeignKey("turmas.id"), primary_key=True)
    nota_final: float = Column(Float, nullable=True)
    status: StatusAprovacaoEnum = Column(
        Enum(StatusAprovacaoEnum), default=StatusAprovacaoEnum.EM_CURSO
    )
    aluno = relationship("Aluno", back_populates="matriculas")
    turma = relationship("Turma", back_populates="matriculas")
    notas_avaliacoes = relationship(
        "NotaAvaliacao", back_populates="matricula", cascade="all, delete-orphan"
    )


class AvaliacaoTurma(Base):
    __tablename__ = "avaliacoes_turma"
    id: int = Column(Integer, primary_key=True, index=True)
    nome: str = Column(String(100), nullable=False)
    id_turma: int = Column(Integer, ForeignKey("turmas.id"), nullable=False)
    turma = relationship("Turma", back_populates="avaliacoes_definidas")
    notas = relationship(
        "NotaAvaliacao", back_populates="avaliacao_turma", cascade="all, delete-orphan"
    )
    __table_args__ = (UniqueConstraint("id_turma", "nome", name="_turma_nome_uc"),)


class NotaAvaliacao(Base):
    __tablename__ = "notas_avaliacoes"
    id: int = Column(Integer, primary_key=True, index=True)
    nota: float = Column(Float, nullable=True)
    id_avaliacao_turma: int = Column(
        Integer, ForeignKey("avaliacoes_turma.id"), nullable=False
    )
    id_matricula_aluno: int = Column(Integer, nullable=False)
    id_matricula_turma: int = Column(Integer, nullable=False)
    avaliacao_turma = relationship("AvaliacaoTurma", back_populates="notas")
    matricula = relationship("Matricula", back_populates="notas_avaliacoes")
    __table_args__ = (
        ForeignKeyConstraint(
            ["id_matricula_aluno", "id_matricula_turma"],
            ["matriculas.id_aluno", "matriculas.id_turma"],
        ),
        UniqueConstraint(
            "id_avaliacao_turma", "id_matricula_aluno", name="_aluno_avaliacao_uc"
        ),
    )


class Aviso(Base):
    __tablename__ = "avisos"
    id: int = Column(Integer, primary_key=True, index=True)
    titulo: str = Column(String(255), nullable=False)
    conteudo: str = Column(Text, nullable=True)
    data_publicacao: DateTime = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
    )
    id_autor: int = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    id_turma: int = Column(Integer, ForeignKey("turmas.id"), nullable=True)
    id_curso: int = Column(Integer, ForeignKey("cursos.id"), nullable=True)
    autor = relationship("Usuario", back_populates="avisos_publicados")
    turma = relationship("Turma", back_populates="avisos")
    curso = relationship("Curso", back_populates="avisos")
