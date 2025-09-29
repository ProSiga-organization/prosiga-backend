
from sqlalchemy.orm import Session
from ..model import Turmas

class TurmasRepository:
    @staticmethod
    def find_all(db: Session) -> list[Turmas]:
        return db.query(Turmas).all()

    @staticmethod
    def save(db: Session, turma: Turmas) -> Turmas:
        if turma.id:
            db.merge(turma)
        else:
            db.add(turma)
        db.commit()
        return turma

    @staticmethod
    def find_by_id(db: Session, id: int) -> Turmas | None:
        return db.query(Turmas).filter(Turmas.id == id).first()
        
    @staticmethod
    def exists_by_id(db: Session, id: int) -> bool:
        return db.query(Turmas.id).filter(Turmas.id == id).first() is not None

    @staticmethod
    def delete_by_id(db: Session, id: int) -> None:
        turma = db.query(Turmas).filter(Turmas.id == id).first()
        if turma is not None:
            db.delete(turma)
            db.commit()