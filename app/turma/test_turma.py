from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import model

AUTH_MOCK_PATH = "app.deps.requests.get"


def mock_auth_response(user_model):
    """Cria um mock de resposta bem-sucedida do serviço de autenticação."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"email": user_model.email, "id": user_model.id}
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_professor_cria_avaliacao_coluna(
    client: TestClient, db_session: Session, setup_matricula_existente: dict
):
    """
    Testa US-015: Professor (dono) cria a "coluna" de avaliação.
    Verifica se a "célula" (NotaAvaliacao) é criada para o aluno existente.
    """
    professor = setup_matricula_existente["professor"]
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]

    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(professor)):
        response = client.post(
            f"/turmas/{turma.id}/avaliacoes", json={"nome": "P1"}, headers=headers
        )

    assert response.status_code == 201
    data_avaliacao = response.json()
    assert data_avaliacao["nome"] == "P1"
    assert data_avaliacao["id_turma"] == turma.id
    id_avaliacao_criada = data_avaliacao["id"]

    celula_nota = (
        db_session.query(model.NotaAvaliacao)
        .filter_by(id_avaliacao_turma=id_avaliacao_criada, id_matricula_aluno=aluno.id)
        .first()
    )

    assert celula_nota is not None
    assert celula_nota.nota is None


def test_professor_nao_cria_avaliacao_turma_alheia(
    client: TestClient,
    db_session: Session,
    setup_matricula_existente: dict,
    mock_coordenador: model.Coordenador,
):
    """
    Testa US-015: Falha (403) ao tentar criar avaliação em turma de outro professor.
    """
    turma = setup_matricula_existente["turma"]

    outro_professor = model.Professor(
        id=99,
        cpf="99988877766",
        nome="Outro Professor",
        email="outro@prof.com",
        senha_hash="hash",
        status=model.StatusContaEnum.ATIVO,
    )
    db_session.add(outro_professor)
    db_session.commit()

    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(outro_professor)):
        response = client.post(
            f"/turmas/{turma.id}/avaliacoes",
            json={"nome": "P-Intrusa"},
            headers=headers,
        )

    assert response.status_code == 403
    assert (
        "Professor não tem permissão para criar avaliações" in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "user_fixture, expected_status, expected_detail",
    [
        ("mock_professor", 200, None),
        ("mock_aluno", 403, "Acesso negado: Apenas para professores"),
        ("mock_coordenador", 403, "Acesso negado: Apenas para professores"),
    ],
)
def test_lancar_nota_celula_permissoes(
    client: TestClient,
    db_session: Session,
    setup_matricula_existente: dict,
    user_fixture: str,
    expected_status: int,
    expected_detail: str | None,
    request,
):
    """
    Testa US-015: Permissões de lançamento de nota.
    - Professor (dono) lança a nota (atualiza a "célula").
    - Aluno falha (403) ao tentar lançar a própria nota.
    - Coordenador falha (403).
    """
    current_user = request.getfixturevalue(user_fixture)
    aluno = setup_matricula_existente["aluno"]
    turma = setup_matricula_existente["turma"]

    avaliacao_p1 = model.AvaliacaoTurma(nome="P1", id_turma=turma.id)
    db_session.add(avaliacao_p1)
    db_session.commit()

    celula_nota = model.NotaAvaliacao(
        id_avaliacao_turma=avaliacao_p1.id,
        id_matricula_aluno=aluno.id,
        id_matricula_turma=turma.id,
        nota=None,
    )
    db_session.add(celula_nota)
    db_session.commit()

    id_celula_antes = celula_nota.id

    payload = {
        "matricula_aluno": aluno.matricula,
        "id_avaliacao_turma": avaliacao_p1.id,
        "nota": 8.5,
    }
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
        response = client.put("/matriculas/notas", json=payload, headers=headers)

    assert response.status_code == expected_status

    if expected_detail:
        assert expected_detail in response.json()["detail"]
    else:
        data_nota = response.json()
        assert data_nota["nota"] == 8.5
        assert data_nota["id"] == id_celula_antes
        db_session.refresh(celula_nota)
        assert celula_nota.nota == 8.5


@pytest.mark.parametrize(
    "filtros, expected_count, expected_codigos",
    [
        ({"id_periodo_letivo": "periodo_1"}, 2, {"T1", "T3"}),
        ({"id_periodo_letivo": "periodo_1", "semestre_ideal": 2}, 0, set()),
        ({"id_periodo_letivo": "periodo_1", "semestre_ideal": 1}, 2, {"T1", "T3"}),
        ({"codigo_disciplina": "COMP102"}, 1, {"T2"}),
        ({"codigo_disciplina": "COMP"}, 3, {"T1", "T2", "T3"}),
    ],
)
def test_aluno_filtra_turmas(
    client: TestClient,
    db_session: Session,
    mock_aluno: model.Aluno,
    setup_filtros: dict,
    filtros: dict,
    expected_count: int,
    expected_codigos: set,
):
    """
    Testa US-018: Aluno filtra turmas por:
    - id_periodo_letivo
    - semestre_ideal
    - codigo_disciplina (parcial)
    """
    params = {}
    for key, value in filtros.items():
        if key == "id_periodo_letivo":
            params[key] = setup_filtros[value].id
        else:
            params[key] = value

    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)):
        response = client.get("/turmas/", params=params, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == expected_count
    if expected_count > 0:
        assert {t["codigo_turma"] for t in data} == expected_codigos


def test_professor_lista_apenas_suas_turmas(
    client: TestClient, db_session: Session, setup_filtros: dict
):
    """
    Testa US-013: Professor (mock_professor) lista suas turmas (GET /turmas/me)
    e NÃO VÊ a turma do 'outro_professor'.
    """
    professor_1 = setup_filtros["prof_1"]
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(professor_1)):
        response = client.get("/turmas/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    codigos_turmas_prof1 = {t["codigo"] for t in data}
    assert codigos_turmas_prof1 == {"T1", "T2"}
    assert "T3" not in codigos_turmas_prof1


@pytest.mark.parametrize(
    "endpoint, user_fixture, expected_status, expected_content_type, expected_filename_part",
    [
        (
            "exportar-csv",
            "mock_professor",
            200,
            "text/csv",
            "notas_turma_",
        ),
        (
            "diario-pdf",
            "mock_professor",
            200,
            "application/pdf",
            "diario_classe_",
        ),
        ("diario-pdf", "mock_aluno", 403, "application/json", None),
        ("diario-pdf", "mock_coordenador", 403, "application/json", None),
    ],
)
def test_professor_exporta_relatorios_turma_permissoes(
    client: TestClient,
    db_session: Session,
    setup_matricula_existente: dict,
    endpoint: str,
    user_fixture: str,
    expected_status: int,
    expected_content_type: str,
    expected_filename_part: str | None,
    request,
):
    """
    Testa US-016: Professor (dono) exporta o CSV de notas da turma.
    Testa US-017: Professor (dono) gera o diário de classe em PDF.
    Testa Segurança: Aluno (403) não pode gerar diário.
    """
    current_user = request.getfixturevalue(user_fixture)
    turma = setup_matricula_existente["turma"]
    headers = {"Authorization": "Bearer fake-token"}
    url = f"/turmas/{turma.id}/{endpoint}"

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
        response = client.get(url, headers=headers)

    assert response.status_code == expected_status
    assert expected_content_type in response.headers["content-type"]

    if expected_status == 200:
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert expected_filename_part in response.headers["content-disposition"]
        assert f"{turma.codigo}" in response.headers["content-disposition"]
        assert len(response.content) > 0
    else:
        assert "Acesso negado: Apenas para professores" in response.json()["detail"]


@pytest.mark.parametrize(
    "user_fixture, http_method, expected_status, expected_detail",
    [
        ("mock_coordenador", "POST", 201, None),
        ("mock_coordenador", "PUT", 200, None),
        ("mock_coordenador", "DELETE", 204, None),
        ("mock_aluno", "POST", 403, "Acesso negado: Apenas para coordenadores."),
        ("mock_professor", "PUT", 403, "Acesso negado: Apenas para coordenadores."),
        ("mock_aluno", "DELETE", 403, "Acesso negado: Apenas para coordenadores."),
    ],
)
def test_coordenador_cria_atualiza_deleta_turma(
    client: TestClient,
    db_session: Session,
    setup_filtros: dict,
    user_fixture: str,
    http_method: str,
    expected_status: int,
    expected_detail: str | None,
    request,
):
    """
    Testa US-010: Coordenador gerencia turmas (CRUD).
    - Testa POST /turmas/ (criar)
    - Testa PUT /turmas/{id} (atualizar)
    - Testa DELETE /turmas/{id} (deletar)
    - Testa permissões (Aluno/Professor não podem)
    """
    current_user = request.getfixturevalue(user_fixture)
    headers = {"Authorization": "Bearer fake-token"}

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
        "id_periodo_letivo": id_periodo,
    }

    if http_method == "POST":
        with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
            response = client.post("/turmas/", json=payload, headers=headers)
        if expected_status == 201:
            data = response.json()
            assert data["codigo"] == "T-ADMIN"
            assert data["vagas"] == 50

    elif http_method in ("PUT", "DELETE"):
        turma_original = setup_filtros["turma_prof1_p1_s1"]
        url = f"/turmas/{turma_original.id}"

        with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
            if http_method == "PUT":
                payload["codigo"] = turma_original.codigo
                payload["vagas"] = 99
                response = client.put(url, json=payload, headers=headers)
                if expected_status == 200:
                    assert response.json()["vagas"] == 99
            elif http_method == "DELETE":
                response = client.delete(url, headers=headers)
                if expected_status == 204:
                    turma_db = db_session.get(model.Turma, turma_original.id)
                    assert turma_db is None

    assert response.status_code == expected_status
    if expected_detail:
        assert expected_detail in response.json()["detail"]


@pytest.mark.parametrize(
    "http_method, expected_status",
    [
        ("PUT", 200),
        ("DELETE", 204),
    ],
)
def test_professor_atualiza_deleta_avaliacao_coluna(
    client: TestClient,
    db_session: Session,
    setup_matricula_existente: dict,
    http_method: str,
    expected_status: int,
):
    """
    Testa US-015: Professor (dono) atualiza ou deleta "coluna" de avaliação.
    - Testa PUT /turmas/avaliacoes/{id}
    - Testa DELETE /turmas/avaliacoes/{id}
    """
    professor = setup_matricula_existente["professor"]
    turma = setup_matricula_existente["turma"]

    avaliacao = model.AvaliacaoTurma(nome="Avaliacao Teste", id_turma=turma.id)
    db_session.add(avaliacao)
    db_session.commit()
    id_avaliacao = avaliacao.id

    headers = {"Authorization": "Bearer fake-token"}
    url = f"/turmas/avaliacoes/{id_avaliacao}"

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(professor)):
        if http_method == "PUT":
            payload = {"nome": "Nome Atualizado"}
            response = client.put(url, json=payload, headers=headers)
            assert response.json()["nome"] == "Nome Atualizado"
            db_session.refresh(avaliacao)
            assert avaliacao.nome == "Nome Atualizado"

        elif http_method == "DELETE":
            response = client.delete(url, headers=headers)
            avaliacao_db = db_session.get(model.AvaliacaoTurma, id_avaliacao)
            assert avaliacao_db is None

    assert response.status_code == expected_status


def test_get_turma_by_id(client: TestClient, db_session: Session, setup_filtros: dict):
    """
    Testa GET /turmas/{id}: Busca uma turma específica pelo ID.
    Não requer autenticação.
    """
    turma_existente = setup_filtros["turma_prof1_p1_s1"]
    response = client.get(f"/turmas/{turma_existente.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == turma_existente.id
    assert data["codigo"] == turma_existente.codigo


def test_get_turma_by_id_not_found(client: TestClient):
    """
    Testa GET /turmas/{id}: Retorna 404 para ID inexistente.
    """
    response = client.get("/turmas/99999")
    assert response.status_code == 404
    assert "Turma não encontrada" in response.json()["detail"]
