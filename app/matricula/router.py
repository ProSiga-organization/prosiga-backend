from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List 
from . import schema as matricula_schema 
from .. import model
from ..database import get_db
from .repository import MatriculaRepository
from ..turma.repository import TurmaRepository
from ..usuario.repository import UsuarioRepository 
from .. import deps

router = APIRouter(
    prefix="/matriculas",
    tags=["Matrículas"]
)

repo = MatriculaRepository()
repo_turma = TurmaRepository()
repo_usuario = UsuarioRepository() 

# --- ENDPOINTS DE MATRÍCULA (ALUNO) ---
@router.post("/", response_model=matricula_schema.MatriculaResponse, status_code=status.HTTP_201_CREATED)
def create_matricula(
    request: matricula_schema.MatriculaCreate, 
    db: Session = Depends(get_db),
    current_user: model.Usuario = Depends(deps.get_current_user)
):
    """(Aluno) Realiza a matrícula do aluno LOGADO em uma turma."""
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
    nova_matricula = repo.create(db, dados_matricula)
    
    return nova_matricula

@router.get("/me", response_model=List[matricula_schema.MatriculaResponse], summary="Lista as matrículas do aluno logado")
def get_my_matriculas(
    db: Session = Depends(get_db),
    current_aluno: model.Aluno = Depends(deps.get_current_aluno)
):
    """(Aluno) Retorna as matrículas do aluno autenticado (incluindo notas e avaliações)."""
    matriculas = repo.get_matriculas_by_aluno(db, id_aluno=current_aluno.id)
    if not matriculas:
        raise HTTPException(status_code=404, detail="Nenhuma matrícula encontrada.")
    return matriculas

# --- ENDPOINTS DE MATRÍCULA (PROFESSOR)---
@router.patch("/{id_turma}/{matricula_aluno}",
              response_model=matricula_schema.MatriculaResponse, 
              summary="Atualiza nota final/status de um aluno")
def update_matricula_status(
    id_turma: int,
    matricula_aluno: str,
    request: matricula_schema.MatriculaUpdate, 
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Atualiza a nota final e/ou o status (APROVADO, REPROVADO) de um aluno,
    identificando-o pela MATRÍCULA.
    """
    # 1. Encontra o aluno pela matrícula
    aluno = repo_usuario.get_aluno_by_matricula(db, matricula=matricula_aluno)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado com esta matrícula.")
    
    # 2. Usa o ID do aluno para encontrar a matrícula
    matricula_db = repo.get_by_aluno_and_turma(db, id_aluno=aluno.id, id_turma=id_turma)
    if not matricula_db:
        raise HTTPException(status_code=404, detail="Matrícula não encontrada para este aluno nesta turma.")

    # 3. Valida permissão do professor
    if matricula_db.turma.id_professor != current_professor.id:
         raise HTTPException(status_code=403, detail="Professor não tem permissão para alterar notas desta turma.")
    
    # 4. Salva as mudanças
    return repo.update_matricula_status(db, matricula_db=matricula_db, update_data=request)


# --- ENDPOINT (PROFESSOR) - LANÇAR/ALTERAR "CÉLULA"  ---

@router.put("/notas", 
            response_model=matricula_schema.NotaAvaliacaoResponse,
            summary="Lança ou atualiza a nota de um aluno em uma avaliação (célula)")
def create_or_update_nota_celula(
    request: matricula_schema.NotaAvaliacaoCreateUpdate, 
    db: Session = Depends(get_db),
    current_professor: model.Professor = Depends(deps.get_current_professor)
):
    """
    (Professor) Lança ou altera a nota de um aluno (por MATRÍCULA) em uma avaliação.
    """
    # 1. Validação: A avaliação (coluna) existe?
    avaliacao_db = repo_turma.get_avaliacao_turma_by_id(db, request.id_avaliacao_turma)
    if not avaliacao_db:
        raise HTTPException(status_code=404, detail="Avaliação (coluna) não encontrada.")

    # 2. Validação: O professor logado é dono da turma desta avaliação?
    if avaliacao_db.turma.id_professor != current_professor.id:
        raise HTTPException(status_code=403, detail="Professor não tem permissão para lançar notas nesta avaliação.")

    # 3. Validação: O aluno (pela matrícula) existe?
    aluno = repo_usuario.get_aluno_by_matricula(db, matricula=request.matricula_aluno)
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado com esta matrícula.")

    # 4. Validação: O aluno (matrícula) existe E pertence à mesma turma da avaliação?
    id_aluno_encontrado = aluno.id
    id_turma_da_avaliacao = avaliacao_db.id_turma
    
    matricula_db = repo.get_by_aluno_and_turma(db, id_aluno=id_aluno_encontrado, id_turma=id_turma_da_avaliacao)
    if not matricula_db:
        raise HTTPException(status_code=404, detail="Matrícula do aluno não encontrada nesta turma.")

    # 5. Se tudo estiver OK, chama o repositório para criar ou atualizar a "célula"
    try:
        return repo.create_or_update_nota(
            db, 
            nota=request.nota,
            id_aluno=id_aluno_encontrado,
            id_avaliacao_turma=request.id_avaliacao_turma,
            id_turma=id_turma_da_avaliacao
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a nota: {e}")