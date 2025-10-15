from sqlalchemy.orm import Session
from .. import model

class MatriculaRepository:

    def get_by_aluno_and_turma(self, db: Session, id_aluno: int, id_turma: int) -> model.Matricula | None:
        """Verifica se um aluno já está matriculado numa turma."""
        return db.query(model.Matricula).filter(
            model.Matricula.id_aluno == id_aluno,
            model.Matricula.id_turma == id_turma
        ).first()

    def get_matriculas_by_turma(self, db: Session, id_turma: int) -> list[model.Matricula]:
        """Retorna todas as matrículas de uma turma específica."""
        return db.query(model.Matricula).filter(model.Matricula.id_turma == id_turma).all()

    def create(self, db: Session, matricula: model.Matricula) -> model.Matricula:
        """Cria uma nova matrícula no banco de dados."""
        db.add(matricula)
        db.commit()
        db.refresh(matricula)
        return matricula