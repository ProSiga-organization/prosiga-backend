from sqlalchemy.orm import Session

from app import model


class PeriodoLetivoRepository:
    """Classe responsável pelas operações de banco de dados para períodos letivos"""

    def get_all(self, db: Session) -> list[model.PeriodoLetivo]:
        """Retorna todos os períodos letivos."""
        return db.query(model.PeriodoLetivo).all()

    def get_by_id(self, db: Session, id: int) -> model.PeriodoLetivo | None:
        """Busca um período letivo pelo ID."""
        return (
            db.query(model.PeriodoLetivo).filter(model.PeriodoLetivo.id == id).first()
        )

    def save(
        self, db: Session, periodo_letivo: model.PeriodoLetivo
    ) -> model.PeriodoLetivo:
        """Salva um novo período letivo ou atualiza um existente."""
        if periodo_letivo.id:
            db.merge(periodo_letivo)  # Atualiza existente
        else:
            db.add(periodo_letivo)  # Cria novo
        db.commit()
        return periodo_letivo

    def delete(self, db: Session, id: int) -> None:
        """Apaga um período letivo pelo ID."""
        periodo = self.get_by_id(db, id)
        if periodo:
            db.delete(periodo)
            db.commit()

    def get_current(self, db: Session) -> model.PeriodoLetivo | None:
        """Encontra o período letivo mais recente."""
        return (
            db.query(model.PeriodoLetivo)
            .order_by(
                model.PeriodoLetivo.ano.desc(), model.PeriodoLetivo.semestre.desc()
            )  # Ordena por ano e semestre decrescente
            .first()
        )
