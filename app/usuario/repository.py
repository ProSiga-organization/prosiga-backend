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

    def get_aluno_para_ativacao(self, db: Session, cpf: str) -> model.Aluno | None:
        """
        Busca um aluno pelo CPF que esteja com status 'NOVO', 
        pronto para o primeiro acesso.
        """
        return db.query(model.Aluno).filter(
            model.Aluno.cpf == cpf,
            model.Aluno.status == model.StatusContaEnum.NOVO
        ).first()

    def ativar_conta_aluno(self, db: Session, aluno_db: model.Aluno, dados_ativacao: schema.PrimeiroAcessoSchema) -> model.Aluno:
        """
        Ativa a conta de um aluno, atualizando email, senha e status.
        """
        hashed_password = get_password_hash(dados_ativacao.senha)
        
        aluno_db.email = dados_ativacao.email
        aluno_db.senha_hash = hashed_password
        aluno_db.status = model.StatusContaEnum.ATIVO
        
        db.commit()
        db.refresh(aluno_db)
        return aluno_db