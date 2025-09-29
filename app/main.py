# app/main.py

from fastapi import FastAPI
from .turma.router import router as turmas_router
# ... importe outros roteadores que você venha a ter

app = FastAPI(
    title="PróSiga API",
    description="API para o sistema de gerenciamento acadêmico PróSiga."
)
app.include_router(turmas_router)

@app.get("/")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
# ...existing code...