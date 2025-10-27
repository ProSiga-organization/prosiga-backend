from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload, selectinload

from .. import deps, model
from ..database import get_db
from ..relatorios import gerador_pdf
from ..usuario.repository import UsuarioRepository
from . import schema
from .repository import PeriodoLetivoRepository

# Define as rotas da API para períodos letivos
router = APIRouter(prefix="/periodos-letivos", tags=["Períodos Letivos"])

# Instâncias dos repositórios para operações no banco
repo = PeriodoLetivoRepository()
repo_usuario = UsuarioRepository()


@router.post(
    "/",
    response_model=schema.PeriodoLetivoResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_periodo_letivo(
    request: schema.PeriodoLetivoCreate,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    """Cria um novo período letivo."""
    # Cria o período letivo no banco
    periodo = repo.save(db, model.PeriodoLetivo(**request.model_dump()))
    return periodo


@router.get("/", response_model=list[schema.PeriodoLetivoResponse])
def get_all_periodos_letivos(db: Session = Depends(get_db)):
    """Lista todos os períodos letivos."""
    return repo.get_all(db)


@router.get("/{id}", response_model=schema.PeriodoLetivoResponse)
def get_periodo_letivo_by_id(id: int, db: Session = Depends(get_db)):
    """Busca um período letivo pelo seu ID."""
    # Busca o período letivo no banco
    periodo = repo.get_by_id(db, id)
    if not periodo:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")
    return periodo


@router.put("/{id}", response_model=schema.PeriodoLetivoResponse)
def update_periodo_letivo(
    id: int,
    request: schema.PeriodoLetivoCreate,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    """Atualiza um período letivo existente."""
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")
    periodo = repo.save(db, model.PeriodoLetivo(id=id, **request.model_dump()))
    return periodo


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_periodo_letivo(
    id: int,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    """Apaga um período letivo."""
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")
    repo.delete(db, id)


@router.get(
    "/{id}/relatorio-ocupacao", summary="Gera o Relatório de Ocupação de Vagas em PDF"
)
def get_relatorio_ocupacao(
    id: int,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    """
    (Coordenador) Gera e retorna um ficheiro PDF com o relatório de
    ocupação de vagas de todas as turmas de um período letivo.
    """
    periodo = repo.get_by_id(db, id)
    if not periodo:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")

    turmas = (
        db.query(model.Turma)
        .options(
            joinedload(model.Turma.disciplina),
            joinedload(model.Turma.professor),
            selectinload(model.Turma.matriculas),
        )
        .filter(model.Turma.id_periodo_letivo == id)
        .all()
    )

    if not turmas:
        raise HTTPException(
            status_code=404, detail="Nenhuma turma encontrada para este período."
        )

    try:
        pdf_buffer = gerador_pdf.gerar_relatorio_ocupacao_pdf(
            periodo=periodo, turmas=turmas
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar o PDF: {e}")

    filename = f"relatorio_ocupacao_{periodo.ano}_{periodo.semestre}.pdf"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)


@router.get(
    "/{id}/relatorio-turmas-professor",
    summary="Gera o Relatório de Turmas por Professor em PDF",
)
def get_relatorio_turmas_professor(
    id: int,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    """
    (Coordenador) Gera e retorna um ficheiro PDF com a distribuição de
    turmas por professor para um período letivo específico.
    """
    periodo = repo.get_by_id(db, id)
    if not periodo:
        raise HTTPException(status_code=404, detail="Período letivo não encontrado.")

    professores = (
        db.query(model.Professor)
        .options(
            joinedload(model.Professor.turmas).options(
                joinedload(model.Turma.disciplina), selectinload(model.Turma.matriculas)
            )
        )
        .all()
    )

    if not professores:
        raise HTTPException(status_code=404, detail="Nenhum professor encontrado.")

    try:
        pdf_buffer = gerador_pdf.gerar_relatorio_turmas_professor_pdf(
            periodo=periodo, professores=professores
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar o PDF Turmas/Professor: {e}"
        )

    filename = f"relatorio_turmas_professor_{periodo.ano}_{periodo.semestre}.pdf"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)
