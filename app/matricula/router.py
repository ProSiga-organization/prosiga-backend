from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List 
from . import schema as matricula_schema
from .. import model
from ..database import get_db
from .repository import MatriculaRepository
from ..turma.repository import TurmaRepository
from .. import deps

router = APIRouter(
    prefix="/matriculas",
    tags=["Matrículas"]
)

repo = MatriculaRepository()
repo_turma = TurmaRepository()

@router.post("/", response_model=matricula_schema.MatriculaResponse, status_code=status.HTTP_201_CREATED)
def create_matricula(
    request: matricula_schema.MatriculaCreate, 
    db: Session = Depends(get_db),
    current_user: model.Usuario = Depends(deps.get_current_user)
):
    """
    (Aluno) Realiza a matrícula do aluno LOGADO em uma turma.
    """
    if not isinstance(current_user, model.Aluno):
        raise HTTPException(status_code=403, detail="Apenas alunos podem se matricular em turmas.")
    
    id_aluno_logado = current_user.id
    
    turma = repo_turma.get_by_id(db, id=request.id_turma)
    if not turma:
        raise HTTPException(status_code=404, detail="Turma não encontrada.")

    matricula_existente = repo.get_by_aluno_and_turma(db, id_aluno=id_aluno_logado, id_turma=request.id_turma)
    if matricula_existente:
        raise HTTPException(status_code=409, detail="Aluno já matriculado nesta turma.")

    matriculas_na_turma = repo.get_matriculas_by_turma(db, id_turma=request.id_turma)
    if len(matriculas_na_turma) >= turma.vagas:
        raise HTTPException(status_code=400, detail="Não há mais vagas disponíveis nesta turma.")

    dados_matricula = model.Matricula(id_aluno=id_aluno_logado, id_turma=request.id_turma)
    
    # Lógica do repositório agora cria a matrícula E as "células" de nota vazias
    nova_matricula = repo.create(db, dados_matricula)
    
    return nova_matricula

@router.get("/me", response_model=List[matricula_schema.MatriculaResponse], summary="Lista as matrículas do aluno logado")
def get_my_matriculas(
    db: Session = Depends(get_db),
    current_aluno: model.Aluno = Depends(deps.get_current_aluno)
):
    """
    (Aluno) Retorna as matrículas do aluno autenticado (incluindo notas e avaliações).
    """
    matriculas = repo.get_matriculas_by_aluno(db, id_aluno=current_aluno.id)
    if not matriculas:
        raise HTTPException(status_code=404, detail="Nenhuma matrícula encontrada.")
    return matriculas

# --- ENDPOINTS DE MATRÍCULA (PROFESSOR) ---

@router.patch("/{id_turma}/{id_aluno}", 
              response_model=matricula_schema.MatriculaResponse, 
              summary="Atualiza nota final/status de um aluno")
def update_matricula_status(
    id_turma: int,
    id_aluno: int,
    request: matricula_schema.MatriculaUpdate, 
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Atualiza a nota final e/ou o status (APROVADO, REPROVADO) de um aluno.
    """
    matricula_db = repo.get_by_aluno_and_turma(db, id_aluno=id_aluno, id_turma=id_turma)
    if not matricula_db:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada.")

    if matricula_db.turma.id_professor != current_professor.id:
         raise HTTPException(status_code=403, detail="Professor não tem permissão para alterar notas desta turma.")
    
    return repo.update_matricula_status(db, matricula_db=matricula_db, update_data=request)


@router.put("/notas", 
            response_model=matricula_schema.NotaAvaliacaoResponse,
            summary="Lança ou atualiza a nota de um aluno em uma avaliação (célula)")
def create_or_update_nota_celula(
    request: matricula_schema.NotaAvaliacaoCreateUpdate,
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Lança ou altera a nota de um aluno específico em uma avaliação específica.
    Este é o endpoint principal para salvar dados da tabela editável.
    """
    # 1. Validação: A avaliação (coluna) existe?
    avaliacao_db = repo_turma.get_avaliacao_turma_by_id(db, request.id_avaliacao_turma)
    if not avaliacao_db:
        raise HTTPException(status_code=404, detail="Avaliação (coluna) não encontrada.")

    # 2. Validação: O professor logado é dono da turma desta avaliação?
    if avaliacao_db.turma.id_professor != current_professor.id:
        raise HTTPException(status_code=403, detail="Professor não tem permissão para lançar notas nesta avaliação.")

    # 3. Validação: O aluno (matrícula) existe E pertence à mesma turma da avaliação?
    matricula_db = repo.get_by_aluno_and_turma(db, id_aluno=request.id_matricula_aluno, id_turma=avaliacao_db.id_turma)
    if not matricula_db:
        raise HTTPException(status_code=404, detail="Matrícula do aluno não encontrada nesta turma.")

    # 4. Se tudo estiver OK, chama o repositório para criar ou atualizar a "célula"
    try:
        return repo.create_or_update_nota(db, request=request)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a nota: {e}")