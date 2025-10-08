
from fastapi import FastAPI
from .usuario.router import router as usuario_router
from .periodo_letivo.router import router as periodo_letivo_router
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PróSiga API", description="API do PróSiga.")
app.include_router(usuario_router)
app.include_router(periodo_letivo_router)
Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "ok"}