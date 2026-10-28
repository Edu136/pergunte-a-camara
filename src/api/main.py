"""API do agente. O endpoint POST /perguntar será implementado na etapa 5."""

from fastapi import FastAPI

app = FastAPI(title="Pergunte à Câmara", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
