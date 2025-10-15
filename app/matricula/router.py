from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schema
from .. import model
from ..database import get_db
from .repository import MatriculaRepository
from ..turma.repository import TurmaRepository

router = APIRouter(
    prefix="/matriculas",
    tags=["Matrículas"]
)

repo = MatriculaRepository()
repo_turma = TurmaRepository()

@router.post("/", response_model=schema.MatriculaResponse, status_code=status.HTTP_201_CREATED)
def create_matricula(request: schema.MatriculaCreate, db: Session = Depends(get_db)):
    """Realiza a matrícula de um aluno em uma turma."""
    
    # 1. Verificar se a turma existe
    turma = repo_turma.get_by_id(db, id=request.id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    # 2. Verificar se o aluno já está matriculado nesta turma
    matricula_existente = repo.get_by_aluno_and_turma(db, id_aluno=request.id_aluno, id_turma=request.id_turma)
    if matricula_existente:
        raise HTTPException(status_code=409, detail="Aluno já matriculado nesta turma.")

    # 3. Verificar se ainda há vagas na turma
    matriculas_na_turma = repo.get_matriculas_by_turma(db, id_turma=request.id_turma)
    if len(matriculas_na_turma) >= turma.vagas:
        raise HTTPException(status_code=400, detail="Não há mais vagas disponíveis nesta turma.")

    # (Validações futuras: pré-requisitos, período de matrícula, etc.)


    nova_matricula = repo.create(db, model.Matricula(**request.model_dump()))
    return nova_matricula