# PróSiga Backend

API principal do Sistema de Gerenciamento Acadêmico - Backend FastAPI

## 🚀 Tecnologias

- **FastAPI** - Framework web Python moderno
- **SQLAlchemy** - ORM Python
- **PostgreSQL** - Banco de dados relacional
- **Pydantic** - Validação de dados
- **Pytest** - Framework de testes
- **Uvicorn** - Servidor ASGI

## 📋 Pré-requisitos

- Python 3.10+
- PostgreSQL 13+
- pip ou poetry para gerenciamento de dependências

## ⚙️ Configuração

### 1. Criar ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DB_CONNECT_URL=postgresql://usuario:senha@localhost:5432/prosiga_db
AUTH_SERVICE_URL=http://localhost:9000/login/me
```

Para produção (Render):
```env
DB_CONNECT_URL=postgresql://prosiga_db_user:senha@host.oregon-postgres.render.com/prosiga_db
AUTH_SERVICE_URL=https://prosiga-login.onrender.com/login/me
```

## 🏃 Executando o projeto

### Opção 1: Desenvolvimento local (sem Docker)

```bash
uvicorn app.main:app --reload --port 8000
```

Acesse:
- API: http://localhost:8000
- Documentação interativa (Swagger): http://localhost:8000/docs
- Documentação alternativa (ReDoc): http://localhost:8000/redoc

### Opção 2: Com Docker 🐳

O projeto possui `Dockerfile` e `docker-compose.yml` configurados.

**Subir todos os serviços (backend + PostgreSQL):**
```bash
docker-compose up --build
```

**Subir em background:**
```bash
docker-compose up -d
```

**Parar os serviços:**
```bash
docker-compose down
```

**Ver logs:**
```bash
docker-compose logs -f backend
```

**Acessar o container:**
```bash
docker exec -it back-prosiga-backend-1 bash
```

**Serviços disponíveis via Docker:**
- Backend API: http://localhost:8000
- PostgreSQL: localhost:5432
- Documentação: http://localhost:8000/docs

### Executar com seed automático

O seed é executado automaticamente ao iniciar a aplicação. Para desabilitar, comente as linhas no `app/main.py`:

```python
# try:
#     seed_data()
# except Exception as e:
#     print(f"Erro ao executar seed: {e}")
```

### Executar seed manualmente

```bash
python -m app.seed
```

## 🗄️ Banco de Dados

### Seed de dados

O seed popula o banco com:

**Cursos (5):**
- Ciência da Computação (CC)
- Engenharia de Software (ES)
- Engenharia da Computação (EC)
- Sistemas de Informação (SI)
- Design Digital (DD)

**Disciplinas (20):**
- Introdução à Programação, Estrutura de Dados, Algoritmos, etc.

**Usuários pré-cadastrados (5):**
| Nome | CPF | Matrícula | Tipo | Status |
|------|-----|-----------|------|--------|
| Bruno Alves | 11122233301 | 20250001 | Aluno | NOVO |
| Carla Dias | 22233344402 | 20250002 | Aluno | NOVO |
| Mariana Costa | 33344455503 | 20250003 | Aluno | NOVO |
| Prof. Ricardo | 44455566604 | - | Professor | NOVO |
| Coord. Helena | 55566677705 | - | Coordenador | NOVO |

**Status NOVO**: Usuário precisa fazer primeiro acesso para definir email/senha e ativar a conta.

### Conectar ao banco local via pgAdmin

1. Abra pgAdmin
2. Clique em "Add New Server"
3. Configure:
   - **Nome**: ProSiga Local
   - **Host**: localhost
   - **Porta**: 5432
   - **Database**: prosiga_db
   - **Usuário**: seu_usuario
   - **Senha**: sua_senha

### Conectar ao banco de produção (Render)

Use a URL externa fornecida pelo Render:
```
postgresql://prosiga_db_user:senha@dpg-xxxxx.oregon-postgres.render.com/prosiga_db
```

## 🧪 Testes

### Rodar todos os testes

```bash
pytest
```

### Rodar testes específicos

```bash
# Teste de um módulo
pytest app/usuario/test_usuario.py

# Teste de uma função específica
pytest app/matricula/test_matricula.py::test_criar_matricula

# Com saída detalhada
pytest -v

# Com cobertura
pytest --cov=app
```

### Estrutura de testes

```
app/
├── aviso/
│   └── test_aviso.py
├── matricula/
│   └── test_matricula.py
├── periodo_letivo/
│   └── test_periodo_letivo.py
└── test_main.py
```

## 📁 Estrutura do projeto

```
back-prosiga/
├── app/
│   ├── main.py                    # Aplicação principal FastAPI
│   ├── config.py                  # Configurações
│   ├── database.py                # Conexão SQLAlchemy
│   ├── model.py                   # Modelos do banco
│   ├── security.py                # Autenticação JWT
│   ├── seed.py                    # Seed de dados
│   ├── deps.py                    # Dependências compartilhadas
│   ├── aviso/                     # Módulo de avisos
│   │   ├── router.py
│   │   ├── repository.py
│   │   ├── schema.py
│   │   └── test_aviso.py
│   ├── curso/                     # Módulo de cursos
│   ├── disciplina/                # Módulo de disciplinas
│   ├── matricula/                 # Módulo de matrículas
│   ├── periodo_letivo/            # Módulo de períodos
│   ├── relatorios/                # Geração de relatórios PDF
│   ├── stats/                     # Estatísticas
│   ├── turma/                     # Módulo de turmas
│   └── usuario/                   # Módulo de usuários
├── requirements.txt               # Dependências Python
├── pytest.ini                     # Configuração do pytest
├── Dockerfile                     # Imagem Docker
└── README.md
```

## 🔌 Endpoints principais

### Usuários
- `POST /usuarios/primeiro-acesso` - Ativar conta (primeira vez)
- `POST /usuarios/upload-csv` - Upload em lote via CSV
- `GET /usuarios/alunos` - Listar alunos
- `GET /usuarios/professores` - Listar professores

### Cursos e Disciplinas
- `GET /cursos` - Listar cursos
- `POST /cursos` - Criar curso
- `GET /disciplinas` - Listar disciplinas
- `POST /disciplinas` - Criar disciplina

### Períodos Letivos
- `GET /periodos-letivos` - Listar períodos
- `POST /periodos-letivos` - Criar período
- `PUT /periodos-letivos/{id}` - Atualizar período
- `DELETE /periodos-letivos/{id}` - Deletar período

### Turmas
- `GET /turmas` - Listar turmas
- `POST /turmas` - Criar turma
- `PUT /turmas/{id}/notas-faltas` - Lançar notas/faltas

### Matrículas
- `POST /matriculas` - Criar matrícula
- `GET /matriculas/aluno/{id}` - Matrículas do aluno

### Avisos
- `GET /avisos` - Listar avisos
- `POST /avisos` - Criar aviso

### Relatórios
- `GET /relatorios/pdf/turma/{id}` - Relatório de turma em PDF
- `GET /relatorios/pdf/periodo/{id}` - Relatório de período em PDF

## 🔒 Autenticação

O backend valida tokens JWT do serviço de autenticação (`prosiga-login`). Para endpoints protegidos:

```python
from app.deps import get_current_user

@router.get("/protegido")
def rota_protegida(current_user: Usuario = Depends(get_current_user)):
    return {"usuario": current_user.nome}
```

## 🌐 CORS

Configurado para aceitar:
- `http://localhost:3000` (desenvolvimento)
- `https://*.vercel.app` (produção e preview deployments)

## 🌐 Deploy

### Render

O projeto está configurado para deploy no Render:

1. Build Command: `pip install -r requirements.txt`
2. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**URL de produção**: https://prosiga-backend.onrender.com

### Variáveis de ambiente no Render

Configure no painel do Render:
- `DB_CONNECT_URL` - URL do banco PostgreSQL
- `AUTH_SERVICE_URL` - URL do serviço de autenticação

## 🔗 Serviços relacionados

- **Frontend**: [prosiga-front](../prosiga-front) - Next.js
- **Serviço de Autenticação**: [prosiga-login](../prosiga-login) - FastAPI

## 🐛 Debugging

### Problemas comuns

**Erro de conexão com banco:**
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Testar conexão
psql -U usuario -d prosiga_db -h localhost
```

**Erro ao executar seed:**
- Limpe o banco e execute novamente
- Verifique logs no console

**Erro 401 em rotas protegidas:**
- Verifique se AUTH_SERVICE_URL está correto
- Confirme que o token JWT é válido

## 📄 Licença

Este projeto é parte do sistema acadêmico PróSiga.
