from sqlalchemy import distinct, tuple_
from sqlalchemy.orm import Session, joinedload, selectinload

from app import model
from app.matricula import schema as matricula_schema


class MatriculaRepository:
    """Classe responsável pelas operações de banco de dados para matrículas"""

    def get_by_aluno_and_turma(
        self, db: Session, id_aluno: int, id_turma: int
    ) -> model.Matricula | None:
        """Verifica se um aluno já está matriculado numa turma."""
        return (
            db.query(model.Matricula)
            .filter(
                model.Matricula.id_aluno == id_aluno,
                model.Matricula.id_turma == id_turma,
            )
            .first()
        )

    def get_matriculas_by_turma(
        self, db: Session, id_turma: int
    ) -> list[model.Matricula]:
        """
        Retorna todas as matrículas de uma turma específica.
        """
        return (
            db.query(model.Matricula)
            .options(
                joinedload(model.Matricula.aluno), # <--- Carrega dados do aluno
                selectinload(model.Matricula.notas_avaliacoes)
            )
            .filter(model.Matricula.id_turma == id_turma)
            .all()
        )

    def create(self, db: Session, matricula: model.Matricula) -> model.Matricula:
        """
        Cria uma nova matrícula no banco de dados.
        IMPORTANTE: Também cria as "células" (NotaAvaliacao) vazias
        para todas as avaliações (colunas) que já existem na turma.
        """
        # 1. Adiciona a matrícula
        db.add(matricula)
        db.flush()  # Garante que a matrícula existe antes de criar as notas

        # 2. Busca todas as avaliações já definidas para esta turma
        avaliacoes_da_turma = (
            db.query(model.AvaliacaoTurma)
            .filter(model.AvaliacaoTurma.id_turma == matricula.id_turma)
            .all()
        )

        # 3. Cria células de nota vazias para cada avaliação existente
        notas_para_criar = []
        for avaliacao in avaliacoes_da_turma:
            notas_para_criar.append(
                model.NotaAvaliacao(
                    nota=None,
                    id_avaliacao_turma=avaliacao.id,
                    id_matricula_aluno=matricula.id_aluno,
                    id_matricula_turma=matricula.id_turma,
                )
            )

        if notas_para_criar:
            db.add_all(notas_para_criar)

        db.commit()
        db.refresh(matricula)
        return matricula

    def get_matriculas_by_aluno(
        self, db: Session, id_aluno: int
    ) -> list[model.Matricula]:
        """Retorna todas as matrículas de um aluno específico."""
        return (
            db.query(model.Matricula)
            .options(
                joinedload(model.Matricula.turma).options(
                    joinedload(model.Turma.disciplina),
                    joinedload(model.Turma.professor)
                ),
                selectinload(model.Matricula.notas_avaliacoes)
            )
            .filter(model.Matricula.id_aluno == id_aluno)
            .all()
        )

    def update_matricula_status(
        self,
        db: Session,
        matricula_db: model.Matricula,
        update_data: matricula_schema.MatriculaUpdate,
    ) -> model.Matricula:
        """Atualiza campos específicos da matrícula (nota_final, status)."""
        # Atualiza apenas os campos enviados na requisição
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(matricula_db, key, value)

        db.commit()
        db.refresh(matricula_db)
        return matricula_db

    def get_nota_by_aluno_and_avaliacao(
        self, db: Session, id_aluno: int, id_avaliacao_turma: int
    ) -> model.NotaAvaliacao | None:
        """Busca uma "célula" de nota específica."""
        return (
            db.query(model.NotaAvaliacao)
            .filter(
                model.NotaAvaliacao.id_matricula_aluno == id_aluno,
                model.NotaAvaliacao.id_avaliacao_turma == id_avaliacao_turma,
            )
            .first()
        )

    def create_or_update_nota(
        self,
        db: Session,
        nota: float | None,
        id_aluno: int,
        id_avaliacao_turma: int,
        id_turma: int,
    ) -> model.NotaAvaliacao:
        """
        Cria ou atualiza a nota de um aluno em uma avaliação (a "célula").
        Recebe IDs puros validados pelo router.
        """
        # Busca se a nota já existe
        nota_db = self.get_nota_by_aluno_and_avaliacao(
            db, id_aluno=id_aluno, id_avaliacao_turma=id_avaliacao_turma
        )

        if nota_db:
            # Atualiza nota existente
            nota_db.nota = nota
        else:
            # Cria nova entrada de nota
            nota_db = model.NotaAvaliacao(
                nota=nota,
                id_avaliacao_turma=id_avaliacao_turma,
                id_matricula_aluno=id_aluno,
                id_matricula_turma=id_turma,
            )
            db.add(nota_db)

        db.commit()
        db.refresh(nota_db)
        return nota_db

    def trancar_matricula(
        self, db: Session, matricula: model.Matricula
    ) -> model.Matricula:
        """
        Altera o status de uma matrícula para TRANCADO.
        """
        matricula.status = model.StatusAprovacaoEnum.TRANCADO
        db.commit()
        db.refresh(matricula)
        return matricula

    def get_periodos_cursados_por_aluno(self, db: Session, id_aluno: int) -> int:
        """
        Calcula o número de semestres letivos distintos em que um aluno
        esteve matriculado (considerando matrículas em turmas com período letivo definido).
        """
        query = (
            db.query(
                distinct(tuple_(model.PeriodoLetivo.ano, model.PeriodoLetivo.semestre))
            )
            .select_from(model.Matricula)
            .join(model.Turma, model.Matricula.id_turma == model.Turma.id)
            .join(
                model.PeriodoLetivo,
                model.Turma.id_periodo_letivo == model.PeriodoLetivo.id,
            )
            .filter(model.Matricula.id_aluno == id_aluno)
        )

        numero_de_periodos_distintos = query.count()
        return numero_de_periodos_distintos

    def calcular_ira(self, db: Session, id_aluno: int) -> float:
        """
        Calcula o IRA simplificado de um aluno na escala 0-5.
        Média simples das notas finais (escala 0-10) das disciplinas concluídas (Aprovado/Reprovado),
        dividida por 2.
        Retorna 5.0 se nenhuma disciplina concluída for encontrada.
        """
        matriculas_concluidas = (
            db.query(model.Matricula)
            .filter(
                model.Matricula.id_aluno == id_aluno,
                model.Matricula.status.in_(
                    [
                        model.StatusAprovacaoEnum.APROVADO,
                        model.StatusAprovacaoEnum.REPROVADO,
                    ]
                ),
                model.Matricula.nota_final.isnot(None),
            )
            .all()
        )

        if not matriculas_concluidas:
            return 5.0

        soma_notas = sum(m.nota_final for m in matriculas_concluidas)
        numero_disciplinas = len(matriculas_concluidas)
        media_0_10 = soma_notas / numero_disciplinas
        ira_0_5 = media_0_10 / 2.0

        return round(ira_0_5, 2)
