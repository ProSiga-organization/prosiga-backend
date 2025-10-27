from fastapi import FastAPI

# Importa os roteadores de cada módulo
from .aviso.router import router as aviso_router
from .curso.router import router as curso_router
from .database import Base, engine
from .matricula.router import router as matricula_router
from .periodo_letivo.router import router as periodo_letivo_router
from .turma.router import router as turma_router
from .usuario.router import router as usuario_router

# Cria as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Inicializa a aplicação FastAPI
app = FastAPI(title="PróSiga API", description="API do PróSiga.")

# Registra todos os roteadores
app.include_router(usuario_router)
app.include_router(periodo_letivo_router)
app.include_router(turma_router)
app.include_router(matricula_router)
app.include_router(aviso_router)
app.include_router(curso_router)


@app.get("/")
def health_check():
    """Endpoint de verificação de saúde da API"""
    return {"status": "ok"}
