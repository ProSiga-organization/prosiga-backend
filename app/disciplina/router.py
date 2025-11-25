from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import deps, model
from app.database import get_db
from app.disciplina.repository import DisciplinaRepository
from app.disciplina import schema

router = APIRouter(prefix="/disciplinas", tags=["Disciplinas"])
repo = DisciplinaRepository()

@router.get("/", response_model=list[schema.DisciplinaResponse])
def get_all_disciplinas(
    db: Session = Depends(get_db),
    current_user: model.Usuario = Depends(deps.get_current_user)
):
    """
    Lista todas as disciplinas cadastradas no sistema.
    Requer autenticação.
    """
    return repo.get_all(db)