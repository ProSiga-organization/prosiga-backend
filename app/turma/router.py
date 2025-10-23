from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from . import schema as turma_schema
from ..usuario import schema as usuario_schema
from .. import model
from ..database import get_db
from .repository import TurmaRepository
from .. import deps
from ..matricula.repository import MatriculaRepository
from ..matricula import schema as matricula_schema
from ..periodo_letivo.repository import PeriodoLetivoRepository

router = APIRouter(
    prefix="/turmas",
    tags=["Turmas"]
)

repo = TurmaRepository()
repo_matricula = MatriculaRepository()
repo_periodo = PeriodoLetivoRepository()

@router.post("/", response_model=turma_schema.TurmaResponse, status_code=status.HTTP_201_CREATED)
def create_turma(request: turma_schema.TurmaCreate, db: Session = Depends(get_db), current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)):
    turma = repo.save(db, model.Turma(**request.model_dump()))
    return turma

@router.get("/", response_model=List[turma_schema.TurmaResponse])
def get_all_turmas(db: Session = Depends(get_db)):
    return repo.get_all(db)

@router.get("/{id}", response_model=turma_schema.TurmaResponse)
def get_turma_by_id(id: int, db: Session = Depends(get_db)):
    turma = repo.get_by_id(db, id)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    return turma

@router.put("/{id}", response_model=turma_schema.TurmaResponse)
def update_turma(id: int, request: turma_schema.TurmaCreate, db: Session = Depends(get_db), current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)):
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    turma = repo.save(db, model.Turma(id=id, **request.model_dump()))
    return turma

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_turma(id: int, db: Session = Depends(get_db), current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)):
    if not repo.get_by_id(db, id):
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    repo.delete(db, id)

@router.get("/me", response_model=List[turma_schema.TurmaResponse], summary="Lista as turmas do professor logado")
def get_my_turmas(
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    turmas = repo.get_turmas_by_professor(db, id_professor=current_professor.id)
    if not turmas:
        raise HTTPException(status_code=404, detail="Nenhuma turma encontrada para o professor logado.")
    return turmas

@router.get("/{id_turma}/matriculas", 
            response_model=List[matricula_schema.MatriculaResponse], 
            summary="Lista todos os alunos matriculados em uma turma")
def get_matriculas_for_turma(
    id_turma: int,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Retorna a lista de alunos (matrículas) em uma turma.
    O 'MatriculaResponse' agora inclui as 'notas_avaliacoes' (células) de cada aluno.
    """
    turma = repo.get_by_id(db, id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    
    if turma.id_professor != current_professor.id:
        raise HTTPException(status_code=403, detail="Professor não tem permissão para ver os alunos desta turma.")

    matriculas = repo_matricula.get_matriculas_by_turma(db, id_turma=id_turma)
    return matriculas

@router.get("/buscar-por-disciplina/{codigo_disciplina}", 
            response_model=List[turma_schema.TurmaBuscaAlunoResponse], # <- MUDANÇA: Agora é uma Lista
            summary="Busca turmas pelo código da DISCIPLINA (Visão do Aluno)")
def buscar_turmas_por_disciplina(
    codigo_disciplina: str,
    db: Session = Depends(get_db),
    current_aluno: model.Aluno = Depends(deps.get_current_aluno)
):
    """
    (Aluno) Busca todas as turmas disponíveis para uma disciplina (ex: "COMP101")
    no período letivo atual.
    """
    # 1. Busca todas as turmas daquela disciplina (já com matrículas e disciplina carregadas)
    turmas_encontradas = repo.get_turmas_by_disciplina_codigo(db, codigo_disciplina=codigo_disciplina)
    if not turmas_encontradas:
        raise HTTPException(status_code=404, detail="Nenhuma turma encontrada para esta disciplina.")

    # 2. Busca o período letivo atual
    periodo_atual = repo_periodo.get_current(db)
    if not periodo_atual:
        raise HTTPException(status_code=400, detail="Período letivo não está configurado.")

    # 3. Determina o status do aluno em relação a esta DISCIPLINA (uma única vez)
    #    (Pega o ID da disciplina da primeira turma encontrada, já que é o mesmo para todas)
    id_disciplina_buscada = turmas_encontradas[0].id_disciplina
    status_base_disciplina = turma_schema.StatusTurmaAluno.A_FAZER
    
    # Busca o histórico de matrículas do aluno
    matriculas_aluno = repo_matricula.get_matriculas_by_aluno(db, id_aluno=current_aluno.id)
    
    # Otimização: Carrega as turmas das matrículas do aluno para checar o ID da disciplina
    turmas_aluno_ids = [m.id_turma for m in matriculas_aluno]
    turmas_cursadas_map = {
        t.id: t.id_disciplina 
        for t in db.query(model.Turma).filter(model.Turma.id.in_(turmas_aluno_ids)).all()
    }

    for m in matriculas_aluno:
        id_disciplina_da_matricula = turmas_cursadas_map.get(m.id_turma)
        if id_disciplina_da_matricula == id_disciplina_buscada:
            if m.status == model.StatusAprovacaoEnum.APROVADO:
                status_base_disciplina = turma_schema.StatusTurmaAluno.JA_CONCLUIDO
                break # Status final
            elif m.status == model.StatusAprovacaoEnum.TRANCADO:
                status_base_disciplina = turma_schema.StatusTurmaAluno.TRANCADO
            elif m.status == model.StatusAprovacaoEnum.EM_CURSO:
                status_base_disciplina = turma_schema.StatusTurmaAluno.CURSANDO

    # 4. Monta a lista de resposta
    lista_resposta = []
    for turma in turmas_encontradas:
        # Filtra apenas turmas do período letivo atual
        if turma.id_periodo_letivo != periodo_atual.id:
            continue
            
        # Calcula vagas (agora é rápido, os dados de 'matriculas' foram pré-carregados)
        vagas_disponiveis = turma.vagas - len(turma.matriculas)

        lista_resposta.append(turma_schema.TurmaBuscaAlunoResponse(
            id_turma=turma.id,
            codigo_turma=turma.codigo,
            vagas_disponiveis=max(0, vagas_disponiveis),
            horario=turma.horario,
            local=turma.local,
            codigo_disciplina=turma.disciplina.codigo,
            nome_disciplina=turma.disciplina.nome,
            descricao=turma.disciplina.descricao,
            semestre_ideal=turma.disciplina.semestre_ideal,
            status_aluno=status_base_disciplina
        ))

    return lista_resposta

@router.post("/{id_turma}/avaliacoes", 
             response_model=turma_schema.AvaliacaoTurmaResponse, 
             status_code=status.HTTP_201_CREATED, 
             summary="Cria uma nova avaliação (coluna) para a turma")
def create_avaliacao_coluna(
    id_turma: int,
    request: turma_schema.AvaliacaoTurmaCreate,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    turma = repo.get_by_id(db, id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")
    if turma.id_professor != current_professor.id:
        raise HTTPException(status_code=403, detail="Professor não tem permissão para criar avaliações nesta turma.")
    
    # Lógica do repositório cria a "coluna" e as "células" vazias
    return repo.create_avaliacao_turma(db, request=request, id_turma=id_turma)

@router.put("/avaliacoes/{id_avaliacao}", 
            response_model=turma_schema.AvaliacaoTurmaResponse, 
            summary="Atualiza o nome de uma avaliação (coluna)")
def update_avaliacao_coluna(
    id_avaliacao: int,
    request: turma_schema.AvaliacaoTurmaBase,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    avaliacao_db = repo.get_avaliacao_turma_by_id(db, id_avaliacao)
    if not avaliacao_db:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    if avaliacao_db.turma.id_professor != current_professor.id:
        raise HTTPException(status_code=403, detail="Professor não tem permissão para editar esta avaliação.")

    return repo.update_avaliacao_turma(db, avaliacao_db=avaliacao_db, request=request)

@router.delete("/avaliacoes/{id_avaliacao}", 
               status_code=status.HTTP_204_NO_CONTENT, 
               summary="Deleta uma avaliação (coluna) e todas as suas notas")
def delete_avaliacao_coluna(
    id_avaliacao: int,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    avaliacao_db = repo.get_avaliacao_turma_by_id(db, id_avaliacao)
    if not avaliacao_db:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada.")
    if avaliacao_db.turma.id_professor != current_professor.id:
        raise HTTPException(status_code=403, detail="Professor não tem permissão para deletar esta avaliação.")

    repo.delete_avaliacao_turma(db, avaliacao_db=avaliacao_db)

@router.get("/{id_turma}/colegas", 
            response_model=List[usuario_schema.ColegaResponse], 
            summary="Lista os colegas de uma turma")
def get_colegas_turma(
    id_turma: int,
    db: Session = Depends(get_db),
    current_aluno: model.Aluno = Depends(deps.get_current_aluno)
):
    """
    (Aluno) Retorna uma lista de colegas (nome e matrícula) matriculados 
    na mesma turma que o aluno logado.
    """
    # 1. Segurança: Verifica se o próprio aluno logado está na turma
    matricula_aluno_logado = repo_matricula.get_by_aluno_and_turma(
        db, 
        id_aluno=current_aluno.id, 
        id_turma=id_turma
    )
    if not matricula_aluno_logado:
        raise HTTPException(status_code=403, detail="Acesso negado. Você não está matriculado nesta turma.")

    # 2. Busca todas as matrículas da turma
    matriculas_da_turma = repo_matricula.get_matriculas_by_turma(db, id_turma=id_turma)

    # 3. Formata a resposta para o schema ColegaResponse
    colegas = []
    for matricula in matriculas_da_turma:
        # Verifica se a relação 'aluno' foi carregada e não é nula
        if matricula.aluno:
            colegas.append(usuario_schema.ColegaResponse(
                nome=matricula.aluno.nome,
                matricula=matricula.aluno.matricula
            ))
            
    return colegas