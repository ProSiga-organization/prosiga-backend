from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importa os roteadores de cada módulo
from app.aviso.router import router as aviso_router
from app.curso.router import router as curso_router
from app.database import Base, engine
from app.matricula.router import router as matricula_router
from app.periodo_letivo.router import router as periodo_letivo_router
from app.turma.router import router as turma_router
from app.usuario.router import router as usuario_router
from app.stats.router import router as stats_router
from app.disciplina.router import router as disciplina_router

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Executa o seed automaticamente na inicialização (apenas se tabelas estiverem vazias)
try:
    from app.seed import seed_data
    seed_data()
except Exception as e:
    print(f"Aviso: Erro ao executar seed: {e}")

# Inicializa a aplicação FastAPI
app = FastAPI(title="PróSiga API", description="API do PróSiga.")

# Lista de origens permitidas para CORS (localhost e produção)
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
    "https://prosiga-frontend.vercel.app",
]

# Adiciona o Middleware CORS com suporte a preview deployments da Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Aceita todos os subdomínios Vercel
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registra todos os roteadores
app.include_router(usuario_router)
app.include_router(periodo_letivo_router)
app.include_router(turma_router)
app.include_router(matricula_router)
app.include_router(aviso_router)
app.include_router(curso_router)
app.include_router(stats_router)
app.include_router(disciplina_router)


@app.get("/")
def health_check():
    """Endpoint de verificação de saúde da API"""
    return {"status": "ok"}
