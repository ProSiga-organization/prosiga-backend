from sqlalchemy.orm import Session
from . import schema 
from .. import model
from ..security import get_password_hash

class UsuarioRepository:

    def get_by_cpf(self, db: Session, cpf: str) -> model.Usuario | None:
        """
        Busca um usuário (de qualquer tipo) pelo CPF.
        """
        return db.query(model.Usuario).filter(model.Usuario.cpf == cpf).first()
    
    def get_by_email(self, db: Session, email: str) -> model.Usuario | None:
        """Busca um usuário (de qualquer tipo) pelo Email."""
        return db.query(model.Usuario).filter(model.Usuario.email == email).first()

    def get_usuario_para_ativacao(self, db: Session, cpf: str) -> model.Usuario | None:
        """
        Busca um usuário (de qualquer tipo) pelo CPF que esteja com status 'NOVO', 
        pronto para o primeiro acesso.
        """
        return db.query(model.Usuario).filter(
            model.Usuario.cpf == cpf,
            model.Usuario.status == model.StatusContaEnum.NOVO
        ).first()

    def ativar_conta(self, db: Session, usuario_db: model.Usuario, dados_ativacao: schema.PrimeiroAcessoSchema) -> model.Usuario:
        """
        Ativa a conta de um usuário (qualquer tipo), atualizando email, senha e status.
        """
        hashed_password = get_password_hash(dados_ativacao.senha)
        
        usuario_db.email = dados_ativacao.email
        usuario_db.senha_hash = hashed_password
        usuario_db.status = model.StatusContaEnum.ATIVO
        
        db.commit()
        db.refresh(usuario_db)
        return usuario_db
    
    def get_aluno_by_matricula(self, db: Session, matricula: str) -> model.Aluno | None:
        """
        Busca um aluno específico pelo número de matrícula.
        """
        return db.query(model.Aluno).filter(model.Aluno.matricula == str(matricula)).first()
    
    def set_usuario_status(self, db: Session, usuario_db: model.Usuario, novo_status: model.StatusContaEnum) -> model.Usuario:
        """
        Altera o status de um usuário (ATIVO, INATIVO).
        """
        usuario_db.status = novo_status
        db.commit()
        db.refresh(usuario_db)
        return usuario_db