import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from app.main import app
from app.database import Base, get_db
from app import model
from app import deps
from datetime import date

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """
    Fixture que cria uma sessão de banco de dados limpa para CADA teste.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session: Session):
    """
    Fixture que cria um TestClient e sobrescreve a dependência get_db
    para usar o banco de dados de teste (db_session).
    """

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_coordenador, None)
    app.dependency_overrides.pop(deps.get_current_professor, None)
    app.dependency_overrides.pop(deps.get_current_aluno, None)

    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(deps.get_current_user, None)
    app.dependency_overrides.pop(deps.get_current_coordenador, None)
    app.dependency_overrides.pop(deps.get_current_professor, None)
    app.dependency_overrides.pop(deps.get_current_aluno, None)

@pytest.fixture
def mock_coordenador(db_session):
    """Cria um coordenador mock no banco de teste."""
    coordenador = model.Coordenador(
        id=1,
        cpf="11111111111",
        nome="Coordenador de Teste",
        email="coord@teste.com",
        senha_hash="hash",
        status=model.StatusContaEnum.ATIVO
    )
    db_session.add(coordenador)
    db_session.commit()
    return coordenador

@pytest.fixture
def mock_professor(db_session):
    """Cria um professor mock no banco de teste."""
    professor = model.Professor(
        id=2,
        cpf="22222222222",
        nome="Professor de Teste",
        email="prof@teste.com",
        senha_hash="hash",
        status=model.StatusContaEnum.ATIVO
    )
    db_session.add(professor)
    db_session.commit()
    return professor

@pytest.fixture
def mock_aluno(db_session):
    """Cria um aluno mock no banco de teste."""
    aluno = model.Aluno(
        id=3,
        cpf="33333333333",
        nome="Aluno de Teste",
        email="aluno@teste.com",
        matricula="2025-TESTE",
        senha_hash="hash",
        status=model.StatusContaEnum.ATIVO
    )
    db_session.add(aluno)
    db_session.commit()
    return aluno

def mock_auth_coordenador(mock_coordenador_fixture: model.Coordenador):
    """Função que retorna o mock do coordenador."""
    def _mock():
        return mock_coordenador_fixture
    return _mock

def mock_auth_professor(mock_professor_fixture: model.Professor):
    """Função que retorna o mock do professor."""
    def _mock():
        return mock_professor_fixture
    return _mock

def mock_auth_aluno(mock_aluno_fixture: model.Aluno):
    """Função que retorna o mock do aluno."""
    def _mock():
        return mock_aluno_fixture
    return _mock

@pytest.fixture
def setup_turmas(db_session: Session, mock_professor: model.Professor):
    """
    Cria um conjunto de dados complexo (Período, Disciplina, Turmas)
    para ser usado nos testes de matrícula e turma.
    """
    periodo = model.PeriodoLetivo(
        ano=2025,
        semestre=1,
        inicio_matricula=date(2025, 1, 1),
        fim_matricula=date(2025, 1, 10),
        fim_trancamento=date(2025, 3, 1)
    )
    
    disciplina = model.Disciplina(
        codigo="COMP101",
        nome="Programação I",
        semestre_ideal=1
    )
    
    db_session.add_all([periodo, disciplina])
    db_session.commit()
    
    turma_com_vaga = model.Turma(
        codigo="T1",
        vagas=1,
        id_disciplina=disciplina.id,
        id_professor=mock_professor.id,
        id_periodo_letivo=periodo.id
    )
    
    turma_sem_vaga = model.Turma(
        codigo="T2",
        vagas=0,
        id_disciplina=disciplina.id,
        id_professor=mock_professor.id,
        id_periodo_letivo=periodo.id
    )
    
    db_session.add_all([turma_com_vaga, turma_sem_vaga])
    db_session.commit()
    
    return {
        "periodo": periodo,
        "disciplina": disciplina,
        "turma_com_vaga": turma_com_vaga,
        "turma_sem_vaga": turma_sem_vaga
    }

@pytest.fixture
def setup_matricula_existente(db_session: Session, mock_aluno: model.Aluno, mock_professor: model.Professor):
    """
    Cria um ambiente completo para testes de notas:
    1. Período, Disciplina
    2. Turma (pertencente ao mock_professor)
    3. Aluno (mock_aluno) JÁ MATRICULADO na Turma.
    """

    periodo = model.PeriodoLetivo(
        ano=2025, semestre=1, inicio_matricula=date(2025,1,1),
        fim_matricula=date(2025,1,10), fim_trancamento=date(2025,3,1)
    )
    disciplina = model.Disciplina(codigo="COMP101", nome="Programação I", semestre_ideal=1)
    db_session.add_all([periodo, disciplina])
    db_session.commit()
    

    turma_professor = model.Turma(
        codigo="T1-PROF",
        vagas=10,
        id_disciplina=disciplina.id,
        id_professor=mock_professor.id, 
        id_periodo_letivo=periodo.id
    )
    db_session.add(turma_professor)
    db_session.commit()

    matricula_repo = model.Matricula(
        id_aluno=mock_aluno.id,
        id_turma=turma_professor.id
    )

    db_session.add(matricula_repo)
    db_session.commit()
    
    return {
        "turma": turma_professor,
        "matricula": matricula_repo,
        "aluno": mock_aluno,
        "professor": mock_professor
    }

@pytest.fixture
def setup_aviso_context(db_session: Session, mock_professor: model.Professor):
    """
    Cria um Curso e uma Turma (pertencente ao mock_professor)
    para os testes do módulo de Avisos.
    """

    curso_cc = model.Curso(codigo="CC", nome="Ciencia da Computacao")
    db_session.add(curso_cc)
    db_session.commit()
    
    periodo = model.PeriodoLetivo(
        ano=2025, semestre=1, inicio_matricula=date(2025,1,1),
        fim_matricula=date(2025,1,10), fim_trancamento=date(2025,3,1)
    )
    disciplina = model.Disciplina(codigo="AVS101", nome="Testes de Aviso", semestre_ideal=1)
    db_session.add_all([periodo, disciplina])
    db_session.commit()

    turma_prof = model.Turma(
        codigo="T-AVISO",
        vagas=10,
        id_disciplina=disciplina.id,
        id_professor=mock_professor.id,
        id_periodo_letivo=periodo.id
    )
    db_session.add(turma_prof)
    db_session.commit()
    
    return {
        "curso": curso_cc,
        "turma": turma_prof
    }

@pytest.fixture
def setup_filtros(db_session: Session, mock_professor: model.Professor):
    """
    Cria um "mundo" complexo para testar filtros de turma (US-018) e
    a visão do professor (US-013).
    
    Cenário:
    - Prof 1 (mock_professor)
    - Prof 2 (outro_professor)
    - Período 2025.1 e 2025.2
    - Disciplina Semestre 1 (COMP101)
    - Disciplina Semestre 2 (COMP102)
    """
    
    # --- Professores ---
    outro_professor = model.Professor(
        id=99, cpf="99988877766", nome="Outro Professor", email="outro@prof.com", 
        senha_hash="hash", status=model.StatusContaEnum.ATIVO
    )
    db_session.add(outro_professor)

    # --- Períodos ---
    periodo_1 = model.PeriodoLetivo(ano=2025, semestre=1, inicio_matricula=date(2025,1,1), fim_matricula=date(2025,1,10), fim_trancamento=date(2025,3,1))
    periodo_2 = model.PeriodoLetivo(ano=2025, semestre=2, inicio_matricula=date(2025,6,1), fim_matricula=date(2025,6,10), fim_trancamento=date(2025,8,1))
    db_session.add_all([periodo_1, periodo_2])

    # --- Disciplinas ---
    disciplina_s1 = model.Disciplina(codigo="COMP101", nome="Programação I", semestre_ideal=1)
    disciplina_s2 = model.Disciplina(codigo="COMP102", nome="Estrutura de Dados", semestre_ideal=2)
    db_session.add_all([disciplina_s1, disciplina_s2])
    db_session.commit() 

    t1_prof1_p1_s1 = model.Turma(
        codigo="T1", vagas=10, id_disciplina=disciplina_s1.id, 
        id_professor=mock_professor.id, id_periodo_letivo=periodo_1.id
    )
    
    t2_prof1_p2_s2 = model.Turma(
        codigo="T2", vagas=10, id_disciplina=disciplina_s2.id, 
        id_professor=mock_professor.id, id_periodo_letivo=periodo_2.id
    )
    
    t3_prof2_p1_s1 = model.Turma(
        codigo="T3", vagas=10, id_disciplina=disciplina_s1.id, 
        id_professor=outro_professor.id, id_periodo_letivo=periodo_1.id
    )
    
    db_session.add_all([t1_prof1_p1_s1, t2_prof1_p2_s2, t3_prof2_p1_s1])
    db_session.commit()
    
    return {
        "prof_1": mock_professor,
        "prof_2": outro_professor,
        "periodo_1": periodo_1,
        "periodo_2": periodo_2,
        "disciplina_s1": disciplina_s1,
        "disciplina_s2": disciplina_s2,
        "turma_prof1_p1_s1": t1_prof1_p1_s1, # Turma T1
        "turma_prof1_p2_s2": t2_prof1_p2_s2, # Turma T2
        "turma_prof2_p1_s1": t3_prof2_p1_s1, # Turma T3
    }