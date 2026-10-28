"""Contrato do cliente de LLM. O provedor é escolhido por LLM_PROVIDER (Strategy)."""

from dataclasses import dataclass, field
from typing import Any, Protocol

from src.config import Settings


class LLMIndisponivel(RuntimeError):
    pass


@dataclass
class ChamadaFerramenta:
    nome: str
    argumentos: dict[str, Any]


@dataclass
class MensagemLLM:
    conteudo: str
    chamadas: list[ChamadaFerramenta] = field(default_factory=list)


class ClienteLLM(Protocol):
    def conversar(
        self, mensagens: list[dict[str, Any]], ferramentas: list[dict[str, Any]]
    ) -> MensagemLLM:
        """Envia a conversa e devolve a próxima mensagem do modelo. Lança LLMIndisponivel."""
        ...


def criar_cliente(config: Settings) -> ClienteLLM:
    if config.llm_provider == "ollama":
        from src.llm.ollama import ClienteOllama

        return ClienteOllama(
            url=config.ollama_url, modelo=config.ollama_model, num_ctx=config.ollama_num_ctx
        )
    raise NotImplementedError(
        f"Provedor de LLM '{config.llm_provider}' ainda não está implementado; "
        "use LLM_PROVIDER=ollama."
    )
