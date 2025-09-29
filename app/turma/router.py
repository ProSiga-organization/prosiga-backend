

from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..model import Turmas
from .repository import TurmasRepository
from .schema import TurmaRequest, TurmaResponse

router = APIRouter(prefix="/turmas", tags=["Turmas"])

# Endpoint para LISTAR todas as turmas
@router.get("/", response_model=list[TurmaResponse])
def get_all_turmas(db: Session = Depends(get_db)):
    turmas = TurmasRepository.find_all(db)
    return [TurmaResponse.from_orm(t) for t in turmas]

# Endpoint para CRIAR uma turma
@router.post("/", response_model=TurmaResponse, status_code=status.HTTP_201_CREATED)
def create_turma(request: TurmaRequest, db: Session = Depends(get_db)):
    turma = TurmasRepository.save(db, Turmas(**request.dict()))
    return TurmaResponse.from_orm(turma)

# Endpoint para EDITAR (atualizar) uma turma
@router.put("/{id}", response_model=TurmaResponse)
def update_turma(id: int, request: TurmaRequest, db: Session = Depends(get_db)):
    if not TurmasRepository.exists_by_id(db, id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")
    turma = TurmasRepository.save(db, Turmas(id=id, **request.dict()))
    return TurmaResponse.from_orm(turma)

# Endpoint para EXCLUIR uma turma
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_turma(id: int, db: Session = Depends(get_db)):
    if not TurmasRepository.exists_by_id(db, id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Turma não encontrada")
    TurmasRepository.delete_by_id(db, id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)