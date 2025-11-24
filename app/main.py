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

# Inicializa a aplicação FastAPI
app = FastAPI(title="PróSiga API", description="API do PróSiga.")

origins = [
    "http://localhost:3000",
    "http://0.0.0.0:3000",
    "http://127.0.0.1:3000",
]

# Adiciona o Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
