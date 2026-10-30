"""Cliente SSE da API usado pela demo (STORY-005): eventos validados e falhas amigáveis."""

import json

import httpx
import pytest

from src.api.cliente import (
    DEMORA,
    FALHA_GENERICA,
    NAO_ACEITA,
    Falha,
    PassoRecebido,
    RespostaRecebida,
    api_fora,
    ler_sse,
    perguntar,
)
from src.config import Settings
from src.schemas import PassoAgente, Resposta

PERGUNTA = "Quanto foi gasto por UF em 2025?"
PASSO = PassoAgente(ferramenta="consultar_sql", descricao="Consulta ao banco de dados",
                    entrada={"sql": "SELECT 1"}, saida="2 linhas", duracao_ms=1234)
GRAFICO = PassoAgente(ferramenta="gerar_grafico", descricao="Escolha automática do gráfico",
                      saida="barra")
RESPOSTA = Resposta(pergunta=PERGUNTA, sql="SELECT 1", dados=[{"uf": "MG", "total": 1.0}],
                    explicacao="Pronto.", fontes=["fonte"], passos=[PASSO, GRAFICO])


def sse(evento, dados):
    texto = dados if isinstance(dados, str) else dados.model_dump_json()
    return f"event: {evento}\ndata: {texto}\n\n".encode()


def config(**valores):
    return Settings(_env_file=None, **valores)


def transporte(*blocos, status=200, erro=None, requisicoes=None):
    def responder(request):
        if requisicoes is not None:
            requisicoes.append(request)
        if erro:
            raise erro("falha simulada", request=request)
        return httpx.Response(status, headers={"content-type": "text/event-stream"},
                              content=iter(blocos))
    return httpx.MockTransport(responder)


def eventos(transp, cfg=None):
    return list(perguntar(PERGUNTA, cfg or config(), transporte=transp))


# --- Happy path ---------------------------------------------------------------------------

def test_h1_stream_vira_eventos_validados():
    recebidos = eventos(transporte(sse("passo", PASSO), sse("passo", GRAFICO),
                                   sse("resposta", RESPOSTA)))

    assert recebidos == [PassoRecebido(PASSO), PassoRecebido(GRAFICO), RespostaRecebida(RESPOSTA)]


def test_h2_leitor_de_sse_separa_eventos_e_ignora_comentarios():
    linhas = "event: passo\ndata: {\"a\": 1}\n\n: comentário\n\nevent: resposta\ndata: {}\n\n"

    assert list(ler_sse(linhas.split("\n"))) == [("passo", '{"a": 1}'), ("resposta", "{}")]


# --- Edge cases ---------------------------------------------------------------------------

def test_e1_cada_evento_chega_assim_que_e_lido():
    lidos = []

    def corpo():
        for bloco in (sse("passo", PASSO), sse("resposta", RESPOSTA)):
            lidos.append(bloco)
            yield bloco

    def responder(request):
        return httpx.Response(200, content=corpo())

    gerador = perguntar(PERGUNTA, config(), transporte=httpx.MockTransport(responder))

    assert next(gerador) == PassoRecebido(PASSO)
    assert len(lidos) == 1
    assert list(gerador) == [RespostaRecebida(RESPOSTA)]


def test_e7_endereco_e_timeouts_vem_da_config():
    requisicoes = []
    cfg = config(api_url="http://api.teste:9000", demo_timeout_s=123)

    eventos(transporte(sse("resposta", RESPOSTA), requisicoes=requisicoes), cfg)

    (requisicao,) = requisicoes
    assert str(requisicao.url) == "http://api.teste:9000/perguntar"
    assert json.loads(requisicao.content) == {"texto": PERGUNTA}
    assert requisicao.extensions["timeout"]["connect"] == 5
    assert requisicao.extensions["timeout"]["read"] == 123


# --- Error cases --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("transp", "antes", "mensagem"),
    [
        pytest.param(transporte(erro=httpx.ConnectError), [], "fora", id="conexao-recusada"),
        pytest.param(transporte(erro=httpx.ReadTimeout), [], DEMORA, id="timeout"),
        pytest.param(transporte(status=422), [], NAO_ACEITA, id="status-422"),
        pytest.param(transporte(status=500), [], FALHA_GENERICA, id="status-500"),
        pytest.param(transporte(sse("passo", PASSO), sse("erro", '{"mensagem": "x"}')),
                     [PassoRecebido(PASSO)], FALHA_GENERICA, id="evento-erro"),
        pytest.param(transporte(sse("passo", PASSO)), [PassoRecebido(PASSO)], FALHA_GENERICA,
                     id="sem-evento-final"),
        pytest.param(transporte(sse("resposta", "{não é json")), [], FALHA_GENERICA,
                     id="json-invalido"),
        pytest.param(transporte(sse("passo", '{"ferramenta": 1}')), [], FALHA_GENERICA,
                     id="fora-do-schema"),
    ],
)
def test_x1_falhas_viram_uma_unica_falha_amigavel(transp, antes, mensagem):
    cfg = config()
    esperada = api_fora(cfg) if mensagem == "fora" else mensagem

    assert eventos(transp, cfg) == [*antes, Falha(esperada)]


def test_x1_mensagem_de_api_fora_cita_o_endereco():
    assert api_fora(config(api_url="http://127.0.0.1:8000")) == (
        "A API não está respondendo em http://127.0.0.1:8000. Verifique se ela está rodando.")
