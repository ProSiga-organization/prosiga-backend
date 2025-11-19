from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import model
from app.database import get_db
from app.periodo_letivo.repository import PeriodoLetivoRepository

router = APIRouter(prefix="/stats", tags=["Estatísticas"])
repo_periodo = PeriodoLetivoRepository()

@router.get("/dashboard", summary="Retorna estatísticas gerais do sistema")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    # current_coordenador: model.Coordenador = Depends(deps.get_current_coordenador)
):
    """
    Retorna contagens totais para o dashboard do administrador.
    """
    total_alunos = db.query(model.Aluno).count()
    total_professores = db.query(model.Professor).count()
    total_disciplinas = db.query(model.Disciplina).count()
    total_cursos = db.query(model.Curso).count()
    
    # Conta matrículas que estão ativas (EM_CURSO)
    matriculas_ativas = db.query(model.Matricula).filter(
        model.Matricula.status == model.StatusAprovacaoEnum.EM_CURSO
    ).count()
    
    # Busca o período atual (o mais recente)
    periodo_atual = repo_periodo.get_current(db)
    periodo_str = f"{periodo_atual.ano}.{periodo_atual.semestre}" if periodo_atual else "N/A"

    return {
        "totalStudents": total_alunos,
        "totalTeachers": total_professores,
        "totalSubjects": total_disciplinas,
        "totalCourses": total_cursos,
        "activeEnrollments": matriculas_ativas,
        "currentPeriod": periodo_str
    }