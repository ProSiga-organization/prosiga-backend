import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from httpx import AsyncClient
from app.main import app 

@pytest.mark.skip(reason="Endpoint de primeiro acesso ainda em desenvolvimento ou a ser refatorado.")
async def test_primeiro_acesso_aluno_sucesso():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        pass

@pytest.mark.skip(reason="Teste para CPF não encontrado ainda não implementado.")
async def test_primeiro_acesso_aluno_cpf_nao_encontrado():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        pass

@pytest.mark.skip(reason="Teste para upload de CSV ainda não implementado.")
async def test_upload_csv_sucesso():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        pass