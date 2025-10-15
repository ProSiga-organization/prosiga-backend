from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schema
from .. import model
from ..database import get_db
from .repository import MatriculaRepository
from ..turma.repository import TurmaRepository
from .. import deps

router = APIRouter(
    prefix="/matriculas",
    tags=["Matrículas"]
)

repo = MatriculaRepository()
repo_turma = TurmaRepository()

@router.post("/", response_model=schema.MatriculaResponse, status_code=status.HTTP_201_CREATED)
def create_matricula(
    request: schema.MatriculaCreate, 
    db: Session = Depends(get_db),
    # Esta dependência executa a validação do token e retorna o usuário logado
    current_user: model.Usuario = Depends(deps.get_current_user)
):
    """
    Realiza a matrícula do aluno LOGADO em uma turma.
    O ID do aluno é obtido automaticamente a partir do token de autenticação.
    """
    # 1. Verificar se o usuário logado é um Aluno
    if not isinstance(current_user, model.Aluno):
        raise HTTPException(status_code=403, detail="Apenas alunos podem se matricular em turmas.")
    
    id_aluno_logado = current_user.id
    
    # 2. As validações seguintes agora usam o ID do usuário logado
    turma = repo_turma.get_by_id(db, id=request.id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    matricula_existente = repo.get_by_aluno_and_turma(db, id_aluno=id_aluno_logado, id_turma=request.id_turma)
    if matricula_existente:
        raise HTTPException(status_code=409, detail="Aluno já matriculado nesta turma.")

    matriculas_na_turma = repo.get_matriculas_by_turma(db, id_turma=request.id_turma)
    if len(matriculas_na_turma) >= turma.vagas:
        raise HTTPException(status_code=400, detail="Não há mais vagas disponíveis nesta turma.")

    # 3. Cria o objeto de matrícula com o ID do aluno logado
    dados_matricula = model.Matricula(id_aluno=id_aluno_logado, id_turma=request.id_turma)
    nova_matricula = repo.create(db, dados_matricula)
    
    return nova_matricula