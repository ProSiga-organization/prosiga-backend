import csv
import io
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app import deps, model
from app.database import get_db
from app.matricula import schema as matricula_schema
from app.matricula.repository import MatriculaRepository
from app.periodo_letivo.repository import PeriodoLetivoRepository
from app.relatorios import gerador_pdf
from app.usuario import schema as usuario_schema
from app.turma import schema as turma_schema
from app.turma.repository import TurmaRepository

router = APIRouter(prefix="/turmas", tags=["Turmas"])

repo = TurmaRepository()
repo_matricula = MatriculaRepository()
repo_periodo = PeriodoLetivoRepository()


@router.post(
    "/", response_model=turma_schema.TurmaResponse, status_code=status.HTTP_201_CREATED
)
def create_turma(
    request: turma_schema.TurmaCreate,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    turma_nova = repo.save(db, model.Turma(**request.model_dump()))
    turma_completa = repo.get_by_id(db, turma_nova.id)
    return turma_completa

# Endpoint para ADMIN listar todas as turmas
@router.get(
    "/admin/list",
    response_model=List[turma_schema.TurmaResponse],
    summary="Lista todas as turmas (Visão do Coordenador)",
)
def get_all_turmas_admin(
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
    id_periodo_letivo: int | None = Query(None),
    codigo_disciplina: str | None = Query(None),
):
    """
    (Coordenador) Retorna a lista completa de turmas, incluindo dados do professor
    e contagem de matrículas.
    """
    turmas = repo.get_all(
        db, 
        id_periodo_letivo=id_periodo_letivo, 
        codigo_disciplina=codigo_disciplina
    )
    
    # Popula o campo calculado qtd_matriculas
    for t in turmas:
        setattr(t, "qtd_matriculas", len(t.matriculas))
        
    return turmas

@router.get(
    "/",
    response_model=List[turma_schema.TurmaBuscaAlunoResponse],
    summary="Filtra todas as turmas disponíveis (Visão do Aluno)",
)
def get_all_turmas(
    db: Session = Depends(get_db),
    current_aluno: model.Aluno = Depends(deps.get_current_aluno),
    id_periodo_letivo: int | None = Query(None),
    semestre_ideal: int | None = Query(None),
    codigo_disciplina: str | None = Query(None),
):
    turmas_encontradas = repo.get_all(
        db,
        id_periodo_letivo=id_periodo_letivo,
        semestre_ideal=semestre_ideal,
        codigo_disciplina=codigo_disciplina,
    )

    matriculas_aluno = repo_matricula.get_matriculas_by_aluno(
        db, id_aluno=current_aluno.id
    )
    turmas_aluno_ids = [m.id_turma for m in matriculas_aluno]

    turmas_cursadas_map = {
        t.id: t.id_disciplina
        for t in db.query(model.Turma)
        .filter(model.Turma.id.in_(turmas_aluno_ids))
        .all()
    }

    disciplina_status_map = {}
    for m in matriculas_aluno:
        id_disciplina = turmas_cursadas_map.get(m.id_turma)
        if not id_disciplina:
            continue

        if m.status == model.StatusAprovacaoEnum.APROVADO:
            disciplina_status_map[id_disciplina] = turma_schema.StatusTurmaAluno.JA_CONCLUIDO
        elif (
            m.status == model.StatusAprovacaoEnum.EM_CURSO
            and id_disciplina not in disciplina_status_map
        ):
            disciplina_status_map[id_disciplina] = turma_schema.StatusTurmaAluno.CURSANDO
        elif (
            m.status == model.StatusAprovacaoEnum.TRANCADO
            and id_disciplina not in disciplina_status_map
        ):
            disciplina_status_map[id_disciplina] = turma_schema.StatusTurmaAluno.TRANCADO

    lista_resposta = []
    for turma in turmas_encontradas:
        vagas_disponiveis = turma.vagas - len(turma.matriculas)
        status_aluno = disciplina_status_map.get(
            turma.id_disciplina, turma_schema.StatusTurmaAluno.A_FAZER
        )

        lista_resposta.append(
            turma_schema.TurmaBuscaAlunoResponse(
                id_turma=turma.id,
                codigo_turma=turma.codigo,
                vagas_disponiveis=max(0, vagas_disponiveis),
                horario=turma.horario,
                local=turma.local,
                codigo_disciplina=turma.disciplina.codigo,
                nome_disciplina=turma.disciplina.nome,
                descricao=turma.disciplina.descricao,
                semestre_ideal=turma.disciplina.semestre_ideal,
                status_aluno=status_aluno,
            )
        )

    return lista_resposta


@router.put("/{id}", response_model=turma_schema.TurmaResponse)
def update_turma(
    id: int,
    request: turma_schema.TurmaCreate,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    turma_existente = repo.get_by_id(db, id)
    if not turma_existente:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    
    repo.save(db, model.Turma(id=id, **request.model_dump()))
    turma_atualizada = repo.get_by_id(db, id)
    return turma_atualizada


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_turma(
    id: int,
    db: Session = Depends(get_db),
    current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador),
):
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    repo.delete(db, id)


@router.get(
    "/me",
    response_model=List[turma_schema.TurmaResponse],
    summary="Lista as turmas do professor logado",
)
def get_my_turmas(
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor),
):
    turmas = repo.get_turmas_by_professor(db, id_professor=current_professor.id)
    if not turmas:
        return []
    
    for t in turmas:
        setattr(t, "qtd_matriculas", len(t.matriculas))
        
    return turmas


@router.get("/{id}", response_model=turma_schema.TurmaResponse)
def get_turma_by_id(id: int, db: Session = Depends(get_db)):
    turma = repo.get_by_id(db, id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return turma


@router.get(
    "/{id_turma}/matriculas",
    response_model=List[matricula_schema.MatriculaResponse],
    summary="Lista todos os alunos matriculados em uma turma",
)
def get_matriculas_for_turma(
    id_turma: int,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor),
):
    turma = repo.get_by_id(db, id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    if turma.id_professor != current_professor.id:
        raise HTTPException(
            status_code=403,
            detail="Professor não tem permissão para ver os alunos desta turma.",
        )

    matriculas = repo_matricula.get_matriculas_by_turma(db, id_turma=id_turma)
    return matriculas


@router.post(
    "/{id_turma}/avaliacoes",
    response_model=turma_schema.AvaliacaoTurmaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova avaliação (coluna) para a turma",
)
def create_avaliacao_coluna(
    id_turma: int,
    request: turma_schema.AvaliacaoTurmaCreate,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor),
):
    turma = repo.get_by_id(db, id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    if turma.id_professor != current_professor.id:
        raise HTTPException(
            status_code=403,
            detail="Professor não tem permissão para criar avaliações nesta turma.",
        )

    return repo.create_avaliacao_turma(db, request=request, id_turma=id_turma)


@router.put(
    "/avaliacoes/{id_avaliacao}",
    response_model=turma_schema.AvaliacaoTurmaResponse,
    summary="Atualiza o nome de uma avaliação (coluna)",
)
def update_avaliacao_coluna(
    id_avaliacao: int,
    request: turma_schema.AvaliacaoTurmaBase,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor),
):
    avaliacao_db = repo.get_avaliacao_turma_by_id(db, id_avaliacao)
    if not avaliacao_db:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    if avaliacao_db.turma.id_professor != current_professor.id:
        raise HTTPException(
            status_code=403,
            detail="Professor não tem permissão para editar esta avaliação.",
        )

    return repo.update_avaliacao_turma(db, avaliacao_db=avaliacao_db, request=request)


@router.delete(
    "/avaliacoes/{id_avaliacao}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deleta uma avaliação (coluna) e todas as suas notas",
)
def delete_avaliacao_coluna(
    id_avaliacao: int,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor),
):
    avaliacao_db = repo.get_avaliacao_turma_by_id(db, id_avaliacao)
    if not avaliacao_db:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    if avaliacao_db.turma.id_professor != current_professor.id:
        raise HTTPException(
            status_code=403,
            detail="Professor não tem permissão para deletar esta avaliação.",
        )

    repo.delete_avaliacao_turma(db, avaliacao_db=avaliacao_db)


@router.get(
    "/{id_turma}/colegas",
    response_model=List[usuario_schema.ColegaResponse],
    summary="Lista os colegas de uma turma",
)
def get_colegas_turma(
    id_turma: int,
    db: Session = Depends(get_db),
    current_aluno: model.Aluno = Depends(deps.get_current_aluno),
):
    matricula_aluno_logado = repo_matricula.get_by_aluno_and_turma(
        db, id_aluno=current_aluno.id, id_turma=id_turma
    )
    if not matricula_aluno_logado:
        raise HTTPException(
            status_code=403,
            detail="Acesso negado. Você não está matriculado nesta turma.",
        )

    matriculas_da_turma = repo_matricula.get_matriculas_by_turma(db, id_turma=id_turma)

    colegas = []
    for matricula in matriculas_da_turma:
        if matricula.aluno:
            colegas.append(
                usuario_schema.ColegaResponse(
                    nome=matricula.aluno.nome, matricula=matricula.aluno.matricula
                )
            )

    return colegas


@router.get(
    "/{id_turma}/exportar-csv", summary="Exporta as notas da turma em formato CSV"
)
def exportar_notas_csv(
    id_turma: int,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor),
):
    turma = (
        db.query(model.Turma)
        .options(joinedload(model.Turma.avaliacoes_definidas))
        .filter(model.Turma.id == id_turma)
        .first()
    )

    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    if turma.id_professor != current_professor.id:
        raise HTTPException(
            status_code=403, detail="Acesso negado: Você não é o professor desta turma."
        )

    matriculas = (
        db.query(model.Matricula)
        .options(
            joinedload(model.Matricula.aluno),
            joinedload(model.Matricula.notas_avaliacoes),
        )
        .filter(model.Matricula.id_turma == id_turma)
        .join(model.Aluno, model.Matricula.id_aluno == model.Aluno.id)
        .order_by(model.Aluno.nome)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    avaliacoes_colunas = sorted(turma.avaliacoes_definidas, key=lambda x: x.id)

    header = ["Matricula", "Aluno", "Status", "Nota Final"]
    header.extend([av.nome for av in avaliacoes_colunas])
    writer.writerow(header)

    for matricula in matriculas:
        if not matricula.aluno:
            continue

        notas_map = {
            nota.id_avaliacao_turma: nota.nota for nota in matricula.notas_avaliacoes
        }

        row = [
            matricula.aluno.matricula,
            matricula.aluno.nome,
            matricula.status.value if matricula.status else "EM_CURSO",
            matricula.nota_final if matricula.nota_final is not None else "",
        ]

        for av in avaliacoes_colunas:
            nota = notas_map.get(av.id)
            row.append(nota if nota is not None else "")

        writer.writerow(row)

    output.seek(0) 

    headers = {
        "Content-Disposition": f"attachment; filename=notas_turma_{turma.codigo}.csv"
    }

    return StreamingResponse(output, media_type="text/csv", headers=headers)


@router.get(
    "/{id_turma}/diario-pdf", summary="Gera o diário de classe da turma em formato PDF"
)
def exportar_diario_pdf(
    id_turma: int,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor),
):
    turma = (
        db.query(model.Turma)
        .options(
            joinedload(model.Turma.avaliacoes_definidas),
            joinedload(model.Turma.disciplina),
            joinedload(model.Turma.professor),
        )
        .filter(model.Turma.id == id_turma)
        .first()
    )

    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    if turma.id_professor != current_professor.id:
        raise HTTPException(
            status_code=403, detail="Acesso negado: Você não é o professor desta turma."
        )

    matriculas = (
        db.query(model.Matricula)
        .options(
            joinedload(model.Matricula.aluno),
            joinedload(model.Matricula.notas_avaliacoes),
        )
        .filter(model.Matricula.id_turma == id_turma)
        .join(model.Aluno, model.Matricula.id_aluno == model.Aluno.id)
        .order_by(model.Aluno.nome)
        .all()
    )

    try:
        pdf_buffer = gerador_pdf.gerar_diario_classe_pdf(
            turma=turma, matriculas=matriculas
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao gerar o PDF do diário: {e}"
        ) from e

    filename = f"diario_classe_{turma.codigo}.pdf"
    headers = {"Content-Disposition": f"attachment; filename={filename}"}

    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers=headers)