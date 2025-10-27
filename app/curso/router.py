from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import deps, model
from app.database import get_db
from app.relatorios import gerador_pdf
from app.curso.repository import CursoRepository

# Define as rotas da API para cursos
router = APIRouter(prefix="/cursos", tags=["Cursos"])

# Instância do repositório para operações no banco
repo = CursoRepository()


@router.get("/relatorio-alunos", summary="Gera o Relatório de Alunos por Curso em PDF")
def get_relatorio_alunos_por_curso(
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    """
    (Coordenador) Gera e retorna um ficheiro PDF listando todos os alunos
    agrupados por curso.
    """
    # Busca todos os cursos com alunos
    cursos = repo.get_all_with_alunos(db)
    if not cursos:
        raise HTTPException(status_code=404, detail="Nenhum curso encontrado.")

    # Gera o PDF com os dados
    try:
        pdf_buffer = gerador_pdf.gerar_relatorio_alunos_curso_pdf(db=db, cursos=cursos)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar o PDF Alunos/Curso: {e}"
        )

    # Configura o download do arquivo
    filename = "relatorio_alunos_por_curso.pdf"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
