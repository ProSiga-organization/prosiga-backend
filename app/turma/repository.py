from sqlalchemy.orm import Session, joinedload, selectinload

from .. import model
from ..model import Disciplina
from . import schema as turma_schema


class TurmaRepository:
    """Classe responsável pelas operações de banco de dados para turmas"""

    def get_all(
        self,
        db: Session,
        id_periodo_letivo: int | None = None,
        semestre_ideal: int | None = None,
        codigo_disciplina: str | None = None,
    ) -> list[model.Turma]:
        """
        Busca todas as turmas com filtros dinâmicos.
        Otimizado para carregar disciplinas e matrículas.
        """
        # Começa a query com o JOIN obrigatório em Disciplina
        query = db.query(model.Turma).join(model.Disciplina)

        # Adiciona filtros condicionalmente
        if id_periodo_letivo:
            query = query.filter(model.Turma.id_periodo_letivo == id_periodo_letivo)

        if semestre_ideal:
            query = query.filter(model.Disciplina.semestre_ideal == semestre_ideal)

        if codigo_disciplina:
            # 'ilike' para busca parcial (ex: "COMP" encontra "COMP101")
            query = query.filter(
                model.Disciplina.codigo.ilike(f"%{codigo_disciplina}%")
            )

        # Adiciona otimizações para carregar dados relacionados
        query = query.options(
            joinedload(model.Turma.disciplina),  # Carrega a disciplina (JOIN)
            selectinload(model.Turma.matriculas),  # Carrega as matrículas (SELECT IN)
        )

        return query.all()

    def get_by_id(self, db: Session, id: int) -> model.Turma | None:
        return db.query(model.Turma).filter(model.Turma.id == id).first()

    def save(self, db: Session, turma: model.Turma) -> model.Turma:
        if turma.id:
            db.merge(turma)
        else:
            db.add(turma)
        db.commit()
        return turma

    def delete(self, db: Session, id: int) -> None:
        turma = self.get_by_id(db, id)
        if turma:
            db.delete(turma)
            db.commit()

    def get_turmas_by_professor(
        self, db: Session, id_professor: int
    ) -> list[model.Turma]:
        """Retorna todas as turmas de um professor específico."""
        return (
            db.query(model.Turma).filter(model.Turma.id_professor == id_professor).all()
        )

    def create_avaliacao_turma(
        self, db: Session, request: turma_schema.AvaliacaoTurmaCreate, id_turma: int
    ) -> model.AvaliacaoTurma:
        """
        Cria uma nova definição de avaliação (coluna) para a turma.
        IMPORTANTE: Também cria as "células" (NotaAvaliacao) vazias
        para todos os alunos já matriculados.
        """
        # 1. Cria a nova avaliação (coluna)
        nova_avaliacao = model.AvaliacaoTurma(nome=request.nome, id_turma=id_turma)
        db.add(nova_avaliacao)
        db.flush()  # Garante que o ID seja gerado

        # 2. Busca alunos já matriculados na turma
        matriculas_da_turma = (
            db.query(model.Matricula).filter(model.Matricula.id_turma == id_turma).all()
        )

        # 3. Cria células de nota vazias para cada aluno matriculado
        notas_para_criar = []
        for matricula in matriculas_da_turma:
            notas_para_criar.append(
                model.NotaAvaliacao(
                    nota=None,
                    id_avaliacao_turma=nova_avaliacao.id,
                    id_matricula_aluno=matricula.id_aluno,
                    id_matricula_turma=matricula.id_turma,
                )
            )

        if notas_para_criar:
            db.add_all(notas_para_criar)

        db.commit()
        db.refresh(nova_avaliacao)
        return nova_avaliacao

    def get_avaliacao_turma_by_id(
        self, db: Session, id_avaliacao: int
    ) -> model.AvaliacaoTurma | None:
        """Busca uma definição de avaliação (coluna) pelo ID."""
        return (
            db.query(model.AvaliacaoTurma)
            .filter(model.AvaliacaoTurma.id == id_avaliacao)
            .first()
        )

    def update_avaliacao_turma(
        self,
        db: Session,
        avaliacao_db: model.AvaliacaoTurma,
        request: turma_schema.AvaliacaoTurmaBase,
    ) -> model.AvaliacaoTurma:
        """Atualiza o nome de uma definição de avaliação (coluna)."""
        avaliacao_db.nome = request.nome
        db.commit()
        db.refresh(avaliacao_db)
        return avaliacao_db

    def delete_avaliacao_turma(
        self, db: Session, avaliacao_db: model.AvaliacaoTurma
    ) -> None:
        """Deleta uma definição de avaliação (coluna). O cascade no modelo deletará as notas."""
        db.delete(avaliacao_db)
        db.commit()
