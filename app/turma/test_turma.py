import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app import deps
from app import model
from app.conftest import mock_auth_professor, mock_auth_aluno, mock_auth_coordenador

def test_professor_cria_avaliacao_coluna(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-015: Professor (dono) cria a "coluna" de avaliação.
    Verifica se a "célula" (NotaAvaliacao) é criada para o aluno existente.
   
    """
    professor = setup_matricula_existente["professor"]
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(professor)
    
    response = client.post(
        f"/turmas/{turma.id}/avaliacoes",
        json={"nome": "P1"}
    )
    
    assert response.status_code == 201
    data_avaliacao = response.json()
    assert data_avaliacao["nome"] == "P1"
    assert data_avaliacao["id_turma"] == turma.id
    id_avaliacao_criada = data_avaliacao["id"]
    
    celula_nota = db_session.query(model.NotaAvaliacao).filter_by(
        id_avaliacao_turma=id_avaliacao_criada,
        id_matricula_aluno=aluno.id
    ).first()
    
    assert celula_nota is not None
    assert celula_nota.nota is None

def test_professor_nao_cria_avaliacao_turma_alheia(client: TestClient, db_session: Session, setup_matricula_existente: dict, mock_coordenador: model.Coordenador):
    """
    Testa US-015: Falha (403) ao tentar criar avaliação em turma de outro professor.
    """
    turma = setup_matricula_existente["turma"] 
    
    outro_professor = model.Professor(
        id=99, cpf="99988877766", nome="Outro Professor", email="outro@prof.com", 
        senha_hash="hash", status=model.StatusContaEnum.ATIVO
    )
    db_session.add(outro_professor)
    db_session.commit()
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(outro_professor)
    response = client.post(
        f"/turmas/{turma.id}/avaliacoes",
        json={"nome": "P-Intrusa"}
    )
    
    assert response.status_code == 403
    assert "Professor não tem permissão para criar avaliações" in response.json()["detail"]

def test_professor_lanca_nota_celula(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-015: Professor lança a nota (atualiza a "célula").
   
    """
    professor = setup_matricula_existente["professor"]
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(professor)
    avaliacao_p1 = model.AvaliacaoTurma(nome="P1", id_turma=turma.id)
    db_session.add(avaliacao_p1)
    db_session.commit()
    
    celula_nota = model.NotaAvaliacao(
        id_avaliacao_turma=avaliacao_p1.id,
        id_matricula_aluno=aluno.id,
        id_matricula_turma=turma.id,
        nota=None
    )
    db_session.add(celula_nota)
    db_session.commit()
    
    id_celula_antes = celula_nota.id

    payload = {
        "matricula_aluno": aluno.matricula, 
        "id_avaliacao_turma": avaliacao_p1.id, 
        "nota": 8.5
    }
    response = client.put("/matriculas/notas", json=payload)
    
    assert response.status_code == 200
    data_nota = response.json()
    assert data_nota["nota"] == 8.5
    assert data_nota["id"] == id_celula_antes 
    
    db_session.refresh(celula_nota)
    assert celula_nota.nota == 8.5

def test_aluno_nao_lanca_propria_nota(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-015: Falha (403) se o Aluno tentar lançar a própria nota.
    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(aluno)
    
    avaliacao_p1 = model.AvaliacaoTurma(nome="P1", id_turma=turma.id)
    db_session.add(avaliacao_p1)
    db_session.commit()

    payload = {
        "matricula_aluno": aluno.matricula,
        "id_avaliacao_turma": avaliacao_p1.id,
        "nota": 10.0 
    }
    response = client.put("/matriculas/notas", json=payload)
    
    assert response.status_code == 403
    assert "Acesso negado: Apenas para professores" in response.json()["detail"]


def test_aluno_filtra_turmas_por_periodo(client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_filtros: dict):
    """
    Testa US-018: Aluno filtra turmas por id_periodo_letivo.
   
    """
    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(mock_aluno)
    id_periodo_1 = setup_filtros["periodo_1"].id
    response = client.get(f"/turmas/?id_periodo_letivo={id_periodo_1}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {t["codigo_turma"] for t in data} == {"T1", "T3"}

def test_aluno_filtra_turmas_por_semestre_ideal(client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_filtros: dict):
    """
    Testa US-018: Aluno filtra turmas por semestre_ideal da disciplina.
   
    """
    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(mock_aluno)
    id_periodo_1 = setup_filtros["periodo_1"].id
    response = client.get(f"/turmas/?id_periodo_letivo={id_periodo_1}&semestre_ideal=2")
    
    assert response.status_code == 200
    assert len(response.json()) == 0
    response_2 = client.get(f"/turmas/?id_periodo_letivo={id_periodo_1}&semestre_ideal=1")

    assert response_2.status_code == 200
    assert len(response_2.json()) == 2

def test_aluno_filtra_turmas_por_codigo_disciplina(client: TestClient, db_session: Session, mock_aluno: model.Aluno, setup_filtros: dict):
    """
    Testa US-018: Aluno busca turmas por código da disciplina (busca parcial 'ilike').
   
    """

    app.dependency_overrides[deps.get_current_aluno] = mock_auth_aluno(mock_aluno)
    response = client.get("/turmas/?codigo_disciplina=COMP102")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["codigo_turma"] == "T2"
    response_2 = client.get("/turmas/?codigo_disciplina=COMP")
    
    assert response_2.status_code == 200
    assert len(response_2.json()) == 3


def test_professor_lista_apenas_suas_turmas(client: TestClient, db_session: Session, setup_filtros: dict):
    """
    Testa US-013: Professor (mock_professor) lista suas turmas (GET /turmas/me)
    e NÃO VÊ a turma do 'outro_professor'.
   
    """

    professor_1 = setup_filtros["prof_1"]
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(professor_1)

    response = client.get("/turmas/me")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    codigos_turmas_prof1 = {t["codigo"] for t in data}
    assert codigos_turmas_prof1 == {"T1", "T2"}
    assert "T3" not in codigos_turmas_prof1

def test_professor_exporta_notas_csv(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-016: Professor (dono) exporta o CSV de notas da turma.
   
    """

    professor = setup_matricula_existente["professor"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(professor)
    response = client.get(f"/turmas/{turma.id}/exportar-csv")
    
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert f"notas_turma_{turma.codigo}.csv" in response.headers["content-disposition"]
    assert len(response.content) > 0

def test_professor_gera_diario_pdf(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa US-017: Professor (dono) gera o diário de classe em PDF.
   
    """
    professor = setup_matricula_existente["professor"]
    turma = setup_matricula_existente["turma"]
    
    app.dependency_overrides[deps.get_current_professor] = mock_auth_professor(professor)
    response = client.get(f"/turmas/{turma.id}/diario-pdf")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert f"diario_classe_{turma.codigo}.pdf" in response.headers["content-disposition"]
    
    assert len(response.content) > 0

def test_aluno_nao_pode_gerar_diario_pdf_do_professor(client: TestClient, db_session: Session, setup_matricula_existente: dict):
    """
    Testa Segurança: Aluno (403) não pode gerar diário de classe do professor.
   
    """
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]

    app.dependency_overrides[deps.get_current_user] = mock_auth_aluno(aluno)

    response = client.get(f"/turmas/{turma.id}/diario-pdf")

    assert response.status_code == 403
    assert "Acesso negado: Apenas para professores" in response.json()["detail"]

def test_coordenador_cria_turma_sucesso(client: TestClient, db_session: Session, mock_coordenador: model.Coordenador, setup_filtros: dict):
    """
    Testa US-010: Coordenador cria uma nova turma.
   
    """
    app.dependency_overrides[deps.get_current_coordenador] = mock_auth_coordenador(mock_coordenador)
    id_disciplina = setup_filtros["disciplina_s1"].id
    id_periodo = setup_filtros["periodo_1"].id
    id_professor = setup_filtros["prof_1"].id
    
    payload = {
        "codigo": "T-ADMIN",
        "vagas": 50,
        "horario": "Seg 19:00-21:00",
        "local": "Sala 101",
        "id_disciplina": id_disciplina,
        "id_professor": id_professor,
        "id_periodo_letivo": id_periodo
    }

    response = client.post("/turmas/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["codigo"] == "T-ADMIN"
    assert data["vagas"] == 50
    assert data["id_professor"] == id_professor