from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from . import schema
from .. import model
from ..database import get_db
from .repository import PeriodoLetivoRepository

router = APIRouter(
    prefix="/periodos-letivos",
    tags=["Períodos Letivos"]
)

repo = PeriodoLetivoRepository()

@router.post("/", response_model=schema.PeriodoLetivoResponse, status_code=status.HTTP_201_CREATED)
def create_periodo_letivo(request: schema.PeriodoLetivoCreate, db: Session = Depends(get_db)):
    """Cria um novo período letivo."""
    periodo = repo.save(db, model.PeriodoLetivo(**request.model_dump()))
    return periodo

@router.get("/", response_model=list[schema.PeriodoLetivoResponse])
def get_all_periodos_letivos(db: Session = Depends(get_db)):
    """Lista todos os períodos letivos."""
    return repo.get_all(db)

@router.get("/{id}", response_model=schema.PeriodoLetivoResponse)
def get_periodo_letivo_by_id(id: int, db: Session = Depends(get_db)):
    """Busca um período letivo pelo seu ID."""
    periodo = repo.get_by_id(db, id)
    if not periodo:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")
    return periodo

@router.put("/{id}", response_model=schema.PeriodoLetivoResponse)
def update_periodo_letivo(id: int, request: schema.PeriodoLetivoCreate, db: Session = Depends(get_db)):
    """Atualiza um período letivo existente."""
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")
    periodo = repo.save(db, model.PeriodoLetivo(id=id, **request.model_dump()))
    return periodo

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_periodo_letivo(id: int, db: Session = Depends(get_db)):
    """Apaga um período letivo."""
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")
    repo.delete(db, id)