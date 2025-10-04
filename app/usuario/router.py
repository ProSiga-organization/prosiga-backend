import csv
import io
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from sqlalchemy.orm import Session
from . import schema
from .. import model
from ..database import get_db
from .repository import UsuarioRepository

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuários"]
)

repo = UsuarioRepository()

# --- ENDPOINT DE PRIMEIRO ACESSO ---
@router.post("/primeiro-acesso/aluno", 
             response_model=schema.AlunoResponse,
             summary="Realiza o primeiro acesso de um aluno")
def primeiro_acesso_aluno(dados_ativacao: schema.PrimeiroAcessoSchema, db: Session = Depends(get_db)):
    aluno_db = repo.get_aluno_para_ativacao(db, cpf=dados_ativacao.cpf)
    if not aluno_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CPF não encontrado ou conta já ativa. Verifique os dados ou contacte a administração."
        )
    aluno_ativado = repo.ativar_conta_aluno(db, aluno_db=aluno_db, dados_ativacao=dados_ativacao)
    return aluno_ativado

# --- ENDPOINT PARA UPLOAD DE CSV ---
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