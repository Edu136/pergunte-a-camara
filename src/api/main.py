"""API do agente: POST /perguntar entrega cada passo e a resposta por Server-Sent Events.

Regras em specs/STORY-004/spec.bdd.md e fluxo no blueprint.
"""

import json
import logging
import queue
import threading
from collections.abc import Callable, Iterator
from functools import lru_cache
from typing import Annotated, Protocol

from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse

from src.agent.agente import Agente
from src.agent.registro import RegistroJSONL
from src.config import settings
from src.llm.cliente import criar_cliente
from src.schemas import PassoAgente, Pergunta, Resposta
from src.tools.consultar_sql import ConsultorSQL

log = logging.getLogger(__name__)

ERRO_INESPERADO = "Erro inesperado ao processar a pergunta."

app = FastAPI(title="Pergunte à Câmara", version="0.1.0")


class Respondedor(Protocol):
    def responder(
        self, pergunta: str, ao_passo: Callable[[PassoAgente], None] | None = None
    ) -> Resposta: ...


def _sse(evento: str, dados: str) -> str:
    return f"event: {evento}\ndata: {dados}\n\n"


def eventos(agente: Respondedor, texto: str) -> Iterator[str]:
    """Roda o agente numa thread e entrega os passos assim que chegam, depois o evento final.

    Gerador síncrono: o Starlette o itera no threadpool, sem bloquear o event loop.
    """
    fila: queue.Queue[tuple[str, str]] = queue.Queue()

    def executar() -> None:
        final = ("erro", json.dumps({"mensagem": ERRO_INESPERADO}, ensure_ascii=False))
        try:
            resposta = agente.responder(
                texto, ao_passo=lambda passo: fila.put(("passo", passo.model_dump_json()))
            )
            final = ("resposta", resposta.model_dump_json())
        except Exception:
            log.exception("Erro inesperado ao responder a pergunta")
        finally:
            fila.put(final)

    threading.Thread(target=executar, daemon=True).start()
    while True:
        evento, dados = fila.get()
        yield _sse(evento, dados)
        if evento != "passo":
            return


@lru_cache
def obter_agente() -> Agente:
    """Instância única: o cache de categorias do agente vale entre perguntas."""
    return Agente(
        llm=criar_cliente(settings),
        consultor=ConsultorSQL(),
        config=settings,
        registro=RegistroJSONL(settings.agente_log_path),
    )


@app.post("/perguntar")
def perguntar(
    pergunta: Pergunta, agente: Annotated[Respondedor, Depends(obter_agente)]
) -> StreamingResponse:
    return StreamingResponse(
        eventos(agente, pergunta.texto),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
