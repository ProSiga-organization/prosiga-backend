from typing import List
from sqlalchemy.orm import Session, selectinload
from app import model

class CursoRepository:
    """Classe responsável pelas operações de banco de dados para cursos"""

    def get_all(self, db: Session) -> List[model.Curso]:
        """Retorna todos os cursos."""
        return db.query(model.Curso).order_by(model.Curso.nome).all()

    def get_all_with_alunos(self, db: Session) -> List[model.Curso]:
        """
        Retorna uma lista de todos os cursos, otimizado para já carregar
        a lista de alunos de cada curso.
        """
        return (
            db.query(model.Curso)
            .options(selectinload(model.Curso.alunos))
            .order_by(model.Curso.nome)
            .all()
        )

    def get_by_id(self, db: Session, id_curso: int) -> model.Curso | None:
        """Busca um curso específico pelo ID."""
        return db.query(model.Curso).filter(model.Curso.id == id_curso).first()