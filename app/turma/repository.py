from sqlalchemy.orm import Session
from .. import model

class TurmaRepository:

    def get_all(self, db: Session) -> list[model.Turma]:
        return db.query(model.Turma).all()

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
    
    def get_turmas_by_professor(self, db: Session, id_professor: int) -> list[model.Turma]:
        """Retorna todas as turmas de um professor específico."""
        return db.query(model.Turma).filter(model.Turma.id_professor == id_professor).all()