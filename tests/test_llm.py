import json

import httpx
import pytest

from src.config import Settings
from src.llm.cliente import ChamadaFerramenta, LLMIndisponivel, criar_cliente
from src.llm.ollama import ClienteOllama

FERRAMENTAS = [{"type": "function", "function": {"name": "consultar_sql", "parameters": {}}}]


def _cliente(responder) -> ClienteOllama:
    http = httpx.Client(transport=httpx.MockTransport(responder))
    return ClienteOllama(url="http://ollama", modelo="qwen2.5:7b", num_ctx=8192, http=http)


def test_envia_ferramentas_e_le_tool_calls():
    requisicoes = []

    def responder(request: httpx.Request) -> httpx.Response:
        requisicoes.append(request)
        return httpx.Response(200, json={"message": {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": "consultar_sql",
                                         "arguments": {"sql": "SELECT 1"}}}],
        }})

    mensagem = _cliente(responder).conversar([{"role": "user", "content": "oi"}], FERRAMENTAS)

    assert requisicoes[0].method == "POST"
    assert requisicoes[0].url == "http://ollama/api/chat"
    corpo = json.loads(requisicoes[0].content)
    assert corpo["model"] == "qwen2.5:7b"
    assert corpo["stream"] is False
    assert corpo["tools"] == FERRAMENTAS
    assert corpo["options"]["temperature"] == 0
    assert corpo["options"]["num_ctx"] == 8192
    assert "seed" in corpo["options"]
    assert mensagem.chamadas == [ChamadaFerramenta("consultar_sql", {"sql": "SELECT 1"})]


def test_le_resposta_final_em_texto():
    def responder(request):
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "Pronto."}})

    mensagem = _cliente(responder).conversar([], FERRAMENTAS)

    assert mensagem.conteudo == "Pronto." and mensagem.chamadas == []


def test_argumentos_em_texto_json_sao_convertidos():
    def responder(request):
        return httpx.Response(200, json={"message": {"content": "", "tool_calls": [
            {"function": {"name": "consultar_sql", "arguments": '{"sql": "SELECT 1"}'}}]}})

    mensagem = _cliente(responder).conversar([], FERRAMENTAS)

    assert mensagem.chamadas[0].argumentos == {"sql": "SELECT 1"}


@pytest.mark.parametrize("falha", [
    lambda request: (_ for _ in ()).throw(httpx.ConnectError("recusada")),
    lambda request: httpx.Response(500, text="erro interno"),
])
def test_falha_de_comunicacao_vira_llm_indisponivel(falha):
    with pytest.raises(LLMIndisponivel):
        _cliente(falha).conversar([], FERRAMENTAS)


def test_fabrica_cria_cliente_ollama():
    assert isinstance(criar_cliente(Settings(_env_file=None)), ClienteOllama)


def test_fabrica_recusa_provedor_nao_implementado():
    with pytest.raises(NotImplementedError, match="openai"):
        criar_cliente(Settings(_env_file=None, llm_provider="openai"))


@pytest.mark.parametrize("corpo", [
    b"nao e json",
    b'{"message": {"tool_calls": [{"nome": "consultar_sql"}]}}',
    b'["lista em vez de objeto"]',
])
def test_resposta_malformada_vira_llm_indisponivel(corpo):
    def responder(request):
        return httpx.Response(200, content=corpo)

    with pytest.raises(LLMIndisponivel, match="resposta inválida"):
        _cliente(responder).conversar([], FERRAMENTAS)


def test_mantem_o_modelo_carregado_pelo_tempo_configurado():
    requisicoes = []

    def responder(request):
        requisicoes.append(request)
        return httpx.Response(200, json={"message": {"content": "ok"}})

    http = httpx.Client(transport=httpx.MockTransport(responder))
    cliente = ClienteOllama(url="http://o", modelo="m", num_ctx=1, http=http, keep_alive="30m")
    cliente.conversar([], FERRAMENTAS)

    assert json.loads(requisicoes[0].content)["keep_alive"] == "30m"


def test_fabrica_usa_timeout_e_keep_alive_da_configuracao():
    config = Settings(_env_file=None, ollama_timeout_s=300, ollama_keep_alive="30m")

    cliente = criar_cliente(config)

    assert cliente.http.timeout.read == 300
    assert cliente.keep_alive == "30m"


def test_padroes_de_timeout_e_keep_alive():
    config = Settings(_env_file=None)
    assert config.ollama_timeout_s == 300 and config.ollama_keep_alive == "30m"
