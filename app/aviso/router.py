# prosiga-backend/app/aviso/router.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import model
from ..database import get_db
from .. import deps
from . import schema
from .repository import AvisoRepository
from ..turma.repository import TurmaRepository

router = APIRouter(
    prefix="/avisos",
    tags=["Avisos"]
)

repo = AvisoRepository()
repo_turma = TurmaRepository()

@router.post("/turma", 
             response_model=schema.AvisoResponse, 
             status_code=status.HTTP_201_CREATED,
             summary="Professor cria um novo aviso para uma turma")
def create_aviso_para_turma(
    request: schema.AvisoTurmaCreate,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Cria um novo aviso e o associa a uma turma específica.
    """
    turma = repo_turma.get_by_id(db, id=request.id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    
    if turma.id_professor != current_professor.id:
        raise HTTPException(
            status_code=403, 
            detail="Acesso negado: Você não é o professor desta turma."
        )

    aviso = repo.create_aviso_turma(db, request=request, id_autor=current_professor.id)
    return aviso

@router.get("/turma/{id_turma}", 
            response_model=List[schema.AvisoResponse],
            summary="Lista todos os avisos de uma turma específica")
def get_avisos_da_turma(
    id_turma: int,
    db: Session = Depends(get_db),
    current_user: model.Usuario = Depends(deps.get_current_user)
):
    """
    (Aluno/Professor) Retorna uma lista de todos os avisos publicados
    para uma turma específica, ordenados do mais recente para o mais antigo.
    """
    avisos = repo.get_avisos_by_turma(db, id_turma=id_turma)
    return avisos

@router.put("/{id_aviso}", 
            response_model=schema.AvisoResponse,
            summary="Professor atualiza um aviso")
def update_aviso(
    id_aviso: int,
    request: schema.AvisoUpdate,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Atualiza o título ou conteúdo de um aviso que ele publicou.
    """
    aviso_db = repo.get_aviso_by_id(db, id_aviso=id_aviso)
    if not aviso_db:
        raise HTTPException(status_code=404, detail="Aviso não encontrado.")

    if aviso_db.id_autor != current_professor.id:
        raise HTTPException(status_code=403, detail="Acesso negado: Você não é o autor deste aviso.")

    return repo.update_aviso(db, aviso_db=aviso_db, request=request)

@router.delete("/{id_aviso}", 
               status_code=status.HTTP_204_NO_CONTENT,
               summary="Professor deleta um aviso")
def delete_aviso(
    id_aviso: int,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Deleta um aviso que ele publicou.
    """
    aviso_db = repo.get_aviso_by_id(db, id_aviso=id_aviso)
    if not aviso_db:
        raise HTTPException(status_code=404, detail="Aviso não encontrado.")

    if aviso_db.id_autor != current_professor.id:
        raise HTTPException(status_code=403, detail="Acesso negado: Você não é o autor deste aviso.")
    
    repo.delete_aviso(db, aviso_db=aviso_db)