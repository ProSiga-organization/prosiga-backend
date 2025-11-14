import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import model
from app.security import verify_password

AUTH_MOCK_PATH = "app.deps.requests.get"


def mock_auth_response(user_model):
    """Cria um mock de resposta bem-sucedida do serviço de autenticação."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"email": user_model.email, "id": user_model.id}
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_primeiro_acesso_sucesso(client: TestClient, db_session: Session):
    """
    Testa o fluxo de US-001: Primeiro acesso com sucesso.
    Um usuário "NOVO" deve conseguir se ativar.
    """
    aluno_novo = model.Aluno(
        cpf="12345678900",
        nome="Aluno Novo Teste",
        matricula="2025-NOVO",
        senha_hash="",
        status=model.StatusContaEnum.NOVO,
    )
    db_session.add(aluno_novo)
    db_session.commit()

    payload = {
        "cpf": "12345678900",
        "email": "aluno.novo@teste.com",
        "senha": "NovaSenha@123",
    }

    response = client.post("/usuarios/primeiro-acesso", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "aluno.novo@teste.com"
    assert data["status"] == "ATIVO"

    db_session.refresh(aluno_novo)
    assert aluno_novo.status == model.StatusContaEnum.ATIVO
    assert aluno_novo.email == "aluno.novo@teste.com"
    assert verify_password("NovaSenha@123", aluno_novo.senha_hash) is True


@pytest.mark.parametrize(
    "cpf, email, senha, expected_status, expected_detail",
    [
        (
            "99999999999",
            "fantasma@teste.com",
            "SenhaInvalida",
            404,
            "CPF não encontrado ou conta já ativa",
        ),
        (
            "33333333333",
            "email.novo@teste.com",
            "NovaSenha",
            404,
            "CPF não encontrado ou conta já ativa",
        ),
    ],
)
def test_primeiro_acesso_falhas(
    client: TestClient,
    mock_aluno: model.Aluno,
    cpf: str,
    email: str,
    senha: str,
    expected_status: int,
    expected_detail: str,
):
    """
    Testa o primeiro acesso com falhas:
    - CPF não encontrado (404).
    - Conta já ATIVA (404).
    """
    payload = {"cpf": cpf, "email": email, "senha": senha}
    response = client.post("/usuarios/primeiro-acesso", json=payload)
    assert response.status_code == expected_status
    assert expected_detail in response.json()["detail"]


@pytest.mark.parametrize(
    "csv_content, expected_status, expected_message",
    [
        (
            "cpf,nome,matricula,tipo_usuario,codigo_curso\n"
            "55511122201,Novo Aluno CSV,2025-CSV1,aluno,CC\n"
            "55511122202,Novo Prof CSV,,professor,\n",
            201,
            "2 novos usuários pré-cadastrados com sucesso!",
        ),
        (
            "cpf,nome,matricula,tipo_usuario,codigo_curso\n"
            "55533344401,Aluno Fake,2025-CSV2,aluno,INVALIDO\n",
            400,
            "Código de curso 'INVALIDO' inválido",
        ),
        (
            "cpf,nome,matricula,tipo_usuario,codigo_curso\n"
            "55511122201,Aluno OK,2025-CSV1,aluno,CC\n"
            "55533344401,Aluno Sem Mat,,aluno,CC\n",
            207,
            "Matrícula em falta para aluno",
        ),
    ],
)
def test_upload_csv_cenarios(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    csv_content: str,
    expected_status: int,
    expected_message: str,
):
    """
    Testa US-005: Upload de CSV de usuários.
    - Sucesso (201).
    - Falha (Curso inválido, 400).
    - Falha (Dados faltando, 400).
    - Sucesso parcial (Um bom, um mau, 207).
    """
    curso_cc = model.Curso(codigo="CC", nome="Ciencia da Computacao")
    db_session.add(curso_cc)
    db_session.commit()

    csv_file = io.BytesIO(csv_content.encode("utf-8"))
    csv_file.seek(0)
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.post(
            "/usuarios/upload-csv",
            files={"file": ("usuarios.csv", csv_file, "text/csv")},
            headers=headers,
        )

    assert response.status_code == expected_status

    if expected_status == 201:
        assert expected_message in response.json()["message"]
        aluno_db = db_session.query(model.Aluno).filter_by(cpf="55511122201").first()
        prof_db = db_session.query(model.Professor).filter_by(cpf="55511122202").first()
        assert aluno_db is not None
        assert prof_db is not None
        assert aluno_db.status == model.StatusContaEnum.NOVO
    else:
        assert expected_message in response.json()["detail"]


@pytest.mark.parametrize(
    "user_fixture, mock_ira, mock_semestre, expected_filename_part, expected_status",
    [
        ("mock_aluno", 4.2, 2, "2025-TESTE", 200),
        ("mock_professor", None, None, None, 403),
    ],
)
def test_gera_proprio_historico_pdf_permissoes(
    client: TestClient,
    db_session: Session,
    setup_matricula_existente: dict,
    user_fixture: str,
    mock_ira: float | None,
    mock_semestre: int | None,
    expected_filename_part: str | None,
    expected_status: int,
    request,
):
    """
    Testa US-021: Geração de histórico acadêmico em PDF.
    - Aluno gera o próprio histórico (200).
    - Professor falha (403).
    """
    current_user = request.getfixturevalue(user_fixture)
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)), patch(
        "app.usuario.router.repo_matricula.get_periodos_cursados_por_aluno",
        return_value=mock_semestre,
    ) as mock_get_periodos, patch(
        "app.usuario.router.repo_matricula.calcular_ira", return_value=mock_ira
    ) as mock_calcular_ira:
        response = client.get("/usuarios/me/historico-pdf", headers=headers)

    assert response.status_code == expected_status

    if expected_status == 200:
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment; filename=" in response.headers["content-disposition"]
        assert (
            f"historico_{expected_filename_part}.pdf"
            in response.headers["content-disposition"]
        )
        mock_get_periodos.assert_called_once_with(db_session, id_aluno=current_user.id)
        mock_calcular_ira.assert_called_once_with(db_session, id_aluno=current_user.id)
    else:
        assert "Acesso negado: Apenas para alunos" in response.json()["detail"]


@pytest.mark.parametrize(
    "user_to_deactivate_fixture, expected_status, expected_detail",
    [
        ("mock_aluno", 200, None),
        ("mock_coordenador", 400, "Não é permitido desativar a própria conta"),
    ],
)
def test_coordenador_desativa_conta_usuario(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    mock_aluno: model.Aluno,
    user_to_deactivate_fixture: str,
    expected_status: int,
    expected_detail: str | None,
    request,
):
    """
    Testa US-006: Coordenador desativa a conta de outro usuário (Aluno).
    Testa US-006: Falha (400) se o Coordenador tentar desativar a si mesmo.
    """
    user_to_deactivate = request.getfixturevalue(user_to_deactivate_fixture)
    assert user_to_deactivate.status == model.StatusContaEnum.ATIVO

    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)):
        response = client.patch(
            f"/usuarios/{user_to_deactivate.cpf}/desativar", headers=headers
        )

    assert response.status_code == expected_status
    if expected_status == 200:
        assert response.json()["status"] == "INATIVO"
        db_session.refresh(user_to_deactivate)
        assert user_to_deactivate.status == model.StatusContaEnum.INATIVO
    else:
        assert expected_detail in response.json()["detail"]


@pytest.mark.parametrize(
    "user_fixture, expected_type, expected_matricula",
    [
        ("mock_aluno", "aluno", "2025-TESTE"),
        ("mock_professor", "professor", None),
        ("mock_coordenador", "coordenador", None),
    ],
)
def test_get_usuario_me_polimorfico(
    client: TestClient,
    db_session: Session,
    user_fixture: str,
    expected_type: str,
    expected_matricula: str | None,
    request,
):
    """
    Testa US-002: Qualquer utilizador autenticado (Aluno, Professor, Coordenador)
    pode obter os seus próprios dados via /usuarios/me.
    """
    current_user = request.getfixturevalue(user_fixture)
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(current_user)):
        response = client.get("/usuarios/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == current_user.id
    assert data["cpf"] == current_user.cpf
    assert data["tipo_usuario"] == expected_type
    if expected_matricula:
        assert data["matricula"] == expected_matricula
    else:
        assert "matricula" not in data


@pytest.mark.parametrize(
    "endpoint, repo_method_to_patch, mock_return_value, expected_response",
    [
        (
            "/usuarios/me/semestre-atual",
            "app.usuario.router.repo_matricula.get_periodos_cursados_por_aluno",
            3,
            {"semestre_atual": 3},
        ),
        (
            "/usuarios/me/ira",
            "app.usuario.router.repo_matricula.calcular_ira",
            3.75,
            {"ira": 3.75},
        ),
    ],
)
def test_get_aluno_me_detalhes(
    client: TestClient,
    db_session: Session,
    mock_aluno: model.Aluno,
    endpoint: str,
    repo_method_to_patch: str,
    mock_return_value,
    expected_response: dict,
):
    """
    Testa US-102 (API): Aluno obtém o semestre atual estimado.
    Testa US-101 (API): Aluno obtém o seu IRA.
    """
    headers = {"Authorization": "Bearer fake-token"}

    with patch(AUTH_MOCK_PATH, return_value=mock_auth_response(mock_aluno)), patch(
        repo_method_to_patch, return_value=mock_return_value
    ) as mock_repo_call:
        response = client.get(endpoint, headers=headers)

    assert response.status_code == 200
    assert response.json() == expected_response
    mock_repo_call.assert_called_once_with(db_session, id_aluno=mock_aluno.id)


def test_coordenador_gera_historico_aluno_especifico_pdf(
    client: TestClient,
    db_session: Session,
    mock_coordenador: model.Coordenador,
    mock_aluno: model.Aluno,
):
    """
    Testa US-012: Coordenador gera o PDF do histórico de um aluno específico.
    """
    headers = {"Authorization": "Bearer fake-token"}

    with patch(
        AUTH_MOCK_PATH, return_value=mock_auth_response(mock_coordenador)
    ), patch(
        "app.usuario.router.repo_matricula.get_periodos_cursados_por_aluno",
        return_value=3,
    ) as mock_get_periodos, patch(
        "app.usuario.router.repo_matricula.calcular_ira", return_value=4.1
    ) as mock_calcular_ira:
        response = client.get(
            f"/usuarios/{mock_aluno.matricula}/historico-pdf", headers=headers
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in response.headers["content-disposition"]
    assert (
        f"historico_{mock_aluno.matricula}.pdf"
        in response.headers["content-disposition"]
    )
    assert len(response.content) > 0

    mock_get_periodos.assert_called_once_with(db_session, id_aluno=mock_aluno.id)
    mock_calcular_ira.assert_called_once_with(db_session, id_aluno=mock_aluno.id)
