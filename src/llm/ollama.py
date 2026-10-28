"""Cliente do Ollama local: POST /api/chat com tool calling, sem streaming."""

import json
from typing import Any

import httpx

from src.llm.cliente import ChamadaFerramenta, LLMIndisponivel, MensagemLLM

# Respostas reprodutíveis, para a avaliação comparar modelos de forma justa.
SEED = 42


def _argumentos(brutos: Any) -> dict[str, Any]:
    """Alguns modelos mandam os argumentos como texto JSON em vez de objeto."""
    if isinstance(brutos, str):
        try:
            brutos = json.loads(brutos)
        except json.JSONDecodeError:
            return {}
    return brutos if isinstance(brutos, dict) else {}


class ClienteOllama:
    def __init__(
        self,
        url: str,
        modelo: str,
        num_ctx: int,
        http: httpx.Client | None = None,
        timeout: float = 120,
    ):
        self.url = url.rstrip("/")
        self.modelo = modelo
        self.num_ctx = num_ctx
        self.http = http or httpx.Client(timeout=timeout)

    def conversar(
        self, mensagens: list[dict[str, Any]], ferramentas: list[dict[str, Any]]
    ) -> MensagemLLM:
        corpo = {
            "model": self.modelo,
            "messages": mensagens,
            "tools": ferramentas,
            "stream": False,
            "options": {"temperature": 0, "seed": SEED, "num_ctx": self.num_ctx},
        }
        try:
            resposta = self.http.post(f"{self.url}/api/chat", json=corpo)
            resposta.raise_for_status()
        except httpx.HTTPError as erro:
            raise LLMIndisponivel(f"Ollama indisponível em {self.url}: {erro}") from erro

        try:
            mensagem = resposta.json()["message"]
            chamadas = [
                ChamadaFerramenta(
                    nome=chamada["function"]["name"],
                    argumentos=_argumentos(chamada["function"].get("arguments")),
                )
                for chamada in mensagem.get("tool_calls") or []
            ]
            return MensagemLLM(conteudo=mensagem.get("content") or "", chamadas=chamadas)
        except (ValueError, KeyError, TypeError, AttributeError) as erro:
            raise LLMIndisponivel(f"Ollama devolveu uma resposta inválida: {erro!r}") from erro
