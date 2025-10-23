from sqlalchemy.orm import Session, joinedload
from .. import model
from . import schema
from typing import List, Optional

class AvisoRepository:

    def create_aviso_turma(self, db: Session, request: schema.AvisoTurmaCreate, id_autor: int) -> model.Aviso:
        """
        Cria um novo aviso no banco de dados, ligado a uma turma e a um autor.
        """
        novo_aviso = model.Aviso(
            titulo=request.titulo,
            conteudo=request.conteudo,
            id_autor=id_autor,
            id_turma=request.id_turma,
            id_curso=None # É um aviso de turma
        )
        db.add(novo_aviso)
        db.commit()
        db.refresh(novo_aviso)
        return novo_aviso

    def create_aviso_curso(self, db: Session, request: schema.AvisoCursoCreate, id_autor: int) -> model.Aviso:
        """
        Cria um novo aviso no banco de dados, ligado a um curso e a um autor.
        """
        novo_aviso = model.Aviso(
            titulo=request.titulo,
            conteudo=request.conteudo,
            id_autor=id_autor,
            id_turma=None, # É um aviso de curso
            id_curso=request.id_curso
        )
        db.add(novo_aviso)
        db.commit()
        db.refresh(novo_aviso)
        return novo_aviso

    def get_aviso_by_id(self, db: Session, id_aviso: int) -> Optional[model.Aviso]:
        """
        Busca um aviso específico pelo seu ID, já carregando o autor.
        """
        return db.query(model.Aviso).options(
            joinedload(model.Aviso.autor) # Otimização para carregar o autor junto
        ).filter(model.Aviso.id == id_aviso).first()

    def update_aviso(self, db: Session, aviso_db: model.Aviso, request: schema.AvisoUpdate) -> model.Aviso:
        """
        Atualiza um aviso existente no banco de dados.
        """
        # Atualiza apenas os campos que foram enviados (não nulos)
        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(aviso_db, key, value)
            
        db.commit()
        db.refresh(aviso_db)
        return aviso_db

    def delete_aviso(self, db: Session, aviso_db: model.Aviso) -> None:
        """
        Remove um aviso do banco de dados.
        """
        db.delete(aviso_db)
        db.commit()

    def get_avisos_by_turma(self, db: Session, id_turma: int) -> List[model.Aviso]:
        """
        Retorna uma lista de todos os avisos de uma turma específica.
        """
        return db.query(model.Aviso).options(
            joinedload(model.Aviso.autor)
        ).filter(
            model.Aviso.id_turma == id_turma
        ).order_by(
            model.Aviso.data_publicacao.desc()
        ).all()

    def get_avisos_by_curso(self, db: Session, id_curso: int) -> List[model.Aviso]:
        """
        Retorna uma lista de todos os avisos de um curso específico.
        """
        return db.query(model.Aviso).options(
            joinedload(model.Aviso.autor)
        ).filter(
            model.Aviso.id_curso == id_curso
        ).order_by(
            model.Aviso.data_publicacao.desc()
        ).all()