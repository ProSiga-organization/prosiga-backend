from typing import List

from sqlalchemy.orm import Session, joinedload, selectinload

from .. import model


class CursoRepository:

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
