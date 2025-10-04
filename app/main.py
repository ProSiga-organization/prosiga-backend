
from fastapi import FastAPI
from .usuario.router import router as usuario_router
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PróSiga API", description="API do PróSiga.")
app.include_router(usuario_router)
Base.metadata.create_all(bind=engine)

@app.get("/")
def health_check():
    return {"status": "ok"}