import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from app.main import app
from app.database import Base, get_db
from app import model
from app import deps

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
    app.dependency_overrides.pop(deps.get_current_coordenador, None)
    app.dependency_overrides.pop(deps.get_current_professor, None)
    app.dependency_overrides.pop(deps.get_current_aluno, None)

    yield TestClient(app)

    app.dependency_overrides.pop(get_db, None)

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