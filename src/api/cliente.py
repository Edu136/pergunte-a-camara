"""Cliente da API POST /perguntar usado pela demo: lê o SSE e entrega eventos já validados.

Nunca lança exceção para quem chama: toda falha vira um evento Falha com mensagem amigável.
Regras em specs/STORY-005/spec.bdd.md (RN3–RN5).
"""

import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from src.config import Settings, settings
from src.schemas import PassoAgente, Resposta

log = logging.getLogger(__name__)

TIMEOUT_CONEXAO_S = 5
DEMORA = "A resposta demorou mais que o esperado. Tente novamente."
NAO_ACEITA = "A pergunta não foi aceita pela API. Revise o texto e tente novamente."
FALHA_GENERICA = "Não foi possível concluir a pergunta. Tente novamente."


def api_fora(config: Settings) -> str:
    return f"A API não está respondendo em {config.api_url}. Verifique se ela está rodando."


@dataclass(frozen=True)
class PassoRecebido:
    passo: PassoAgente


@dataclass(frozen=True)
class RespostaRecebida:
    resposta: Resposta


@dataclass(frozen=True)
class Falha:
    mensagem: str


Evento = PassoRecebido | RespostaRecebida | Falha


def ler_sse(linhas: Iterable[str]) -> Iterator[tuple[str, str]]:
    """Agrupa as linhas em (evento, data). Comentários (":") são ignorados; um bloco só vale
    quando termina na linha em branco."""
    evento, dados = None, []
    for linha in linhas:
        if not linha:
            if evento and dados:
                yield evento, "\n".join(dados)
            evento, dados = None, []
        elif linha.startswith("event:"):
            evento = linha.removeprefix("event:").strip()
        elif linha.startswith("data:"):
            dados.append(linha.removeprefix("data:").removeprefix(" "))


def perguntar(
    texto: str, config: Settings = settings, transporte: httpx.BaseTransport | None = None
) -> Iterator[Evento]:
    """Envia a pergunta e devolve os passos assim que chegam e, por último, um evento final."""
    timeout = httpx.Timeout(config.demo_timeout_s, connect=TIMEOUT_CONEXAO_S)
    try:
        with (
            httpx.Client(base_url=config.api_url, timeout=timeout, transport=transporte) as cliente,
            cliente.stream("POST", "/perguntar", json={"texto": texto}) as resposta,
        ):
            if resposta.status_code != 200:
                log.warning("API respondeu %s", resposta.status_code)
                yield Falha(NAO_ACEITA if resposta.status_code == 422 else FALHA_GENERICA)
                return
            for evento, dados in ler_sse(resposta.iter_lines()):
                if evento == "passo":
                    yield PassoRecebido(PassoAgente.model_validate_json(dados))
                elif evento == "resposta":
                    yield RespostaRecebida(Resposta.model_validate_json(dados))
                    return
                elif evento == "erro":
                    log.warning("API enviou evento de erro: %s", dados)
                    yield Falha(FALHA_GENERICA)
                    return
            log.warning("Stream da API terminou sem evento final")
            yield Falha(FALHA_GENERICA)
    except (httpx.ConnectError, httpx.ConnectTimeout) as erro:
        log.warning("API inacessível em %s: %s", config.api_url, erro)
        yield Falha(api_fora(config))
    except httpx.TimeoutException as erro:
        log.warning("Tempo de espera da API esgotado: %s", erro)
        yield Falha(DEMORA)
    except (httpx.HTTPError, ValidationError) as erro:
        log.warning("Falha ao ler o stream da API: %s", erro)
        yield Falha(FALHA_GENERICA)
