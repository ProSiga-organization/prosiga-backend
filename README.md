# Backend ProSiga

Este projeto é o backend do ProSiga, utilizando Python (FastAPI), PostgreSQL e pgAdmin, tudo rodando via Docker.

## Pré-requisitos

- Docker
- Docker Compose

## Como iniciar o ambiente

1. **Clone o repositório:**
```bash
git clone <url-do-repositorio>
cd back-prosiga
```

2. **Configure suas variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

3. **Construa e suba os containers:**
```bash
docker-compose up --build
```

## Serviços disponíveis

- **Backend FastAPI**: http://localhost:8000
  - Documentação da API: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 
  - Login conforme configurado no arquivo `.env`
- **PostgreSQL**: localhost:5432

## Estrutura do projeto
```
├── app/                    # Código fonte do backend
│   └── main.py            # Arquivo principal FastAPI
├── .env                   # Variáveis de ambiente (NÃO versionar)
├── .env.example          # Template das variáveis de ambiente
├── docker-compose.yml    # Orquestração dos containers
├── Dockerfile           # Imagem do backend Python
├── requirements.txt     # Dependências Python
└── README.md           # Documentação
```

## Dependências principais
- FastAPI: Framework web para Python
- Uvicorn: Servidor ASGI
- psycopg2-binary: Driver PostgreSQL para Python

## Desenvolvimento

### Adicionar dependências
1. Adicione a dependência no `requirements.txt`
2. Reconstrua o container: `docker-compose up --build`

### Conectar ao banco via pgAdmin
1. Acesse http://localhost:5050
2. Adicione um novo servidor com:
   - Host: `db`
   - Porta: `5432`
   - Usuário: conforme `.env`
   - Senha: conforme `.env`
   - Database: conforme `.env`

## Comandos úteis

```bash
# Subir apenas o banco de dados
docker-compose up db

# Ver logs de um serviço específico
docker-compose logs backend

# Parar todos os serviços
docker-compose down

# Limpar volumes (CUIDADO: apaga dados do banco)
docker-compose down -v
```
