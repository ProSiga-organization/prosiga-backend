import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from . import schema
from .. import model
from ..database import get_db
from .repository import UsuarioRepository
from .. import deps

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

repo = UsuarioRepository()

@router.post("/primeiro-acesso", 
             response_model=schema.AnyUsuarioResponse,
             summary="Realiza o primeiro acesso de qualquer usuário (Aluno, Professor, Coordenador)")
def primeiro_acesso_usuario(dados_ativacao: schema.PrimeiroAcessoSchema, db: Session = Depends(get_db)):
    
    usuario_db = repo.get_usuario_para_ativacao(db, cpf=dados_ativacao.cpf)
    
    if not usuario_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CPF não encontrado ou conta já ativa. Verifique os dados ou contacte a administração."
        )
    
    usuario_ativado = repo.ativar_conta(db, usuario_db=usuario_db, dados_ativacao=dados_ativacao)
    
    return usuario_ativado

@router.get("/me", response_model=schema.AnyUsuarioResponse, summary="Obtém os dados do usuário logado")
def read_users_me(current_user: model.Usuario = Depends(deps.get_current_user)):
    """
    Retorna os dados do usuário que está autenticado (seja Aluno, Professor ou Coordenador).
    """
    return current_user

@router.post("/upload-csv", 
             summary="Pré-cadastra novos usuários a partir de um ficheiro CSV",
             status_code=status.HTTP_201_CREATED)
def upload_usuarios_csv(db: Session = Depends(get_db), file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="O ficheiro tem de ser um CSV.")
    try:
        content = file.file.read().decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(content))
        novos_usuarios = []
        for row in csv_reader:
            cpf = row.get('cpf')
            if not cpf: continue
            
            usuario_existente = repo.get_by_cpf(db, cpf=cpf)
            if usuario_existente:
                print(f"Usuário com CPF {cpf} já existe. A ignorar.")
                continue

            tipo_usuario = row.get('tipo_usuario')
            if tipo_usuario == 'aluno':
                novo_usuario = model.Aluno(cpf=cpf, nome=row['nome'], matricula=row['matricula'], senha_hash="", status=model.StatusContaEnum.NOVO)
            elif tipo_usuario == 'professor':
                novo_usuario = model.Professor(cpf=cpf, nome=row['nome'], senha_hash="", status=model.StatusContaEnum.NOVO)
            elif tipo_usuario == 'coordenador':
                novo_usuario = model.Coordenador(cpf=cpf, nome=row['nome'], senha_hash="", status=model.StatusContaEnum.NOVO)
            else:
                continue
            novos_usuarios.append(novo_usuario)

        if not novos_usuarios:
            return {"message": "Nenhum novo usuário para adicionar."}
        
        db.add_all(novos_usuarios)
        db.commit()
        return {"message": f"{len(novos_usuarios)} novos usuários pré-cadastrados com sucesso!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ocorreu um erro ao processar o ficheiro: {e}")
    
@router.patch("/{cpf}/desativar", 
             response_model=schema.AnyUsuarioResponse,
             summary="Desativa a conta de um usuário pelo CPF")
def desativar_usuario(
    cpf: str,
    db: Session = Depends(get_db),
    # Esta dependência garante que apenas um Coordenador pode executar
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)
):
    """
    (Coordenador) Desativa a conta de um usuário (Aluno, Professor ou outro Coordenador). 
    Um usuário desativado não poderá mais fazer login no serviço de autenticação.
    """
    # 1. Encontra o usuário que será desativado
    usuario_db = repo.get_by_cpf(db, cpf=cpf)
    if not usuario_db:
        raise HTTPException(status_code=404, detail="Usuário não encontrado com este CPF.")
    
    # 2. Regra de negócio: Um coordenador não pode desativar a si mesmo.
    if usuario_db.cpf == current_coordenador.cpf:
        raise HTTPException(status_code=400, detail="Não é permitido desativar a própria conta.")
    
    # 3. Chama o novo método do repositório para alterar o status
    usuario_desativado = repo.set_usuario_status(
        db, 
        usuario_db=usuario_db, 
        novo_status=model.StatusContaEnum.INATIVO
    )
    
    return usuario_desativado