from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from .. import model
from ..database import get_db
from .. import deps
from .repository import CursoRepository
from ..relatorios import gerador_pdf

router = APIRouter(
    prefix="/cursos",
    tags=["Cursos"]
)

repo = CursoRepository()


@router.get("/relatorio-alunos",
            summary="Gera o Relatório de Alunos por Curso em PDF")
def get_relatorio_alunos_por_curso(
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)
):
    """
    (Coordenador) Gera e retorna um ficheiro PDF listando todos os alunos
    agrupados por curso.
    """
    cursos = repo.get_all_with_alunos(db)
    if not cursos:
        raise HTTPException(status_code=404, detail="Nenhum curso encontrado.")

    try:
        pdf_buffer = gerador_pdf.gerar_relatorio_alunos_curso_pdf(
            db=db,
            cursos=cursos
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o PDF Alunos/Curso: {e}")

    filename = "relatorio_alunos_por_curso.pdf"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }

    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)