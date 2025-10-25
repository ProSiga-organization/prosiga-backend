import pytest
from unittest.mock import MagicMock, patch
from app.matricula.repository import MatriculaRepository
from app import model

def test_calcular_ira_sem_disciplinas():
    """
    Testa US-101: Cálculo de IRA para aluno sem histórico.
    O IRA deve ser 5.0 (o valor inicial).
    """
    mock_db = MagicMock()

    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = []
    mock_db.query.return_value = mock_query
    
    repo = MatriculaRepository()
    id_aluno_teste = 1
    
    ira = repo.calcular_ira(db=mock_db, id_aluno=id_aluno_teste)
    
    assert ira == 5.0

def test_calcular_ira_com_historico():
    """
    Testa US-101: Cálculo de IRA com notas.
    IRA = (Média das notas 0-10) / 2
    """
    mock_db = MagicMock()
    
    m1 = MagicMock(spec=model.Matricula)
    m1.nota_final = 10.0
    m1.status = model.StatusAprovacaoEnum.APROVADO
    
    m2 = MagicMock(spec=model.Matricula)
    m2.nota_final = 5.0 
    m2.status = model.StatusAprovacaoEnum.REPROVADO
    
    m3 = MagicMock(spec=model.Matricula)
    m3.nota_final = 8.0
    m3.status = model.StatusAprovacaoEnum.APROVADO

    m4_em_curso = MagicMock(spec=model.Matricula)
    m4_em_curso.nota_final = None
    m4_em_curso.status = model.StatusAprovacaoEnum.EM_CURSO

    mock_query = MagicMock()
    mock_query.filter.return_value.all.return_value = [m1, m2, m3]
    mock_db.query.return_value = mock_query

    repo = MatriculaRepository()
    id_aluno_teste = 1
    ira = repo.calcular_ira(db=mock_db, id_aluno=id_aluno_teste)
    assert ira == 3.83