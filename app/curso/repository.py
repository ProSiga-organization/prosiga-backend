from typing import List

from sqlalchemy.orm import Session, selectinload

from app import model


class CursoRepository:
    """Classe responsável pelas operações de banco de dados para cursos"""

    def get_all_with_alunos(self, db: Session) -> List[model.Curso]:
        """
        Retorna uma lista de todos os cursos, otimizado para já carregar
        a lista de alunos de cada curso.
        """
        return (
            db.query(model.Curso)
            .options(selectinload(model.Curso.alunos))  # Carrega alunos junto
            .order_by(model.Curso.nome)  # Ordenado alfabeticamente
            .all()
        )

    def get_by_id(self, db: Session, id_curso: int) -> model.Curso | None:
        """Busca um curso específico pelo ID."""
        return db.query(model.Curso).filter(model.Curso.id == id_curso).first()
