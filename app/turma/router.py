from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schema
from .. import model
from ..database import get_db
from .repository import TurmaRepository
from .. import deps

router = APIRouter(
    prefix="/turmas",
    tags=["Turmas"]
)

repo = TurmaRepository()

@router.post("/", response_model=schema.TurmaResponse, status_code=status.HTTP_201_CREATED)
def create_turma(request: schema.TurmaCreate, db: Session = Depends(get_db), current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)):
    # Adicionar validações aqui no futuro (ex: verificar se o professor e a disciplina existem)
    turma = repo.save(db, model.Turma(**request.model_dump(), coordenador_id=current_coordenador.id))
    return turma

@router.get("/", response_model=list[schema.TurmaResponse])
def get_all_turmas(db: Session = Depends(get_db)):
    return repo.get_all(db)

@router.get("/{id}", response_model=schema.TurmaResponse)
def get_turma_by_id(id: int, db: Session = Depends(get_db)):
    turma = repo.get_by_id(db, id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return turma

@router.put("/{id}", response_model=schema.TurmaResponse)
def update_turma(id: int, request: schema.TurmaCreate, db: Session = Depends(get_db), current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)):
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    turma = repo.save(db, model.Turma(id=id, **request.model_dump(), coordenador_id=current_coordenador.id))
    return turma

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_turma(id: int, db: Session = Depends(get_db), current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)):
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    repo.delete(db, id)

@router.get("/me", response_model=list[schema.TurmaResponse], summary="Lista as turmas do professor logado")
def get_my_turmas(
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):

    turmas = repo.get_turmas_by_professor(db, id_professor=current_professor.id)
    if not turmas:
        raise HTTPException(status_code=404, detail="Nenhuma turma encontrada para o professor logado.")
    return turmas