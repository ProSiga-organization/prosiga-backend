from sqlalchemy.orm import Session
from app import model

class DisciplinaRepository:
    def get_all(self, db: Session) -> list[model.Disciplina]:
        return db.query(model.Disciplina).order_by(model.Disciplina.nome).all()