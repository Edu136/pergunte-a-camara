"""API POST /perguntar ponta a ponta (STORY-004), com o agente real e LLM/banco falsos."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.agent.agente import (
    BANCO_FORA,
    CORRECOES_ESGOTADAS,
    FONTE_CEAP,
    LIMITE_PASSOS,
    LLM_FORA,
    SEM_DADOS,
    Agente,
)
from src.agent.registro import RegistroJSONL
from src.api.main import ERRO_INESPERADO, app, obter_agente
from src.config import settings
from src.llm.cliente import LLMIndisponivel
from src.schemas import PassoAgente, Resposta
from src.tools.consultar_sql import BancoIndisponivel
from tests.test_agente import LINHAS_UF, SQL_UF, ConsultorFalso, LLMRoteirizado, config, sql, texto
from tests.test_api_eventos import AgenteRoteirizado, ler

PERGUNTA = {"texto": "Quanto cada UF gastou em 2025?"}
SQL_PROIBIDO = "DROP TABLE despesas"


@pytest.fixture
def cliente():
    yield TestClient(app)
    app.dependency_overrides.clear()


def usar(agente):
    app.dependency_overrides[obter_agente] = lambda: agente
    return agente


def perguntar(cliente, corpo=PERGUNTA):
    resposta = cliente.post("/perguntar", json=corpo)
    return resposta, ler([resposta.text])


def test_health(cliente):
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


# --- Happy path ---------------------------------------------------------------------------

def test_h1_h3_pergunta_respondida_vira_stream_de_passos_e_resposta(cliente):
    usar(Agente(llm=LLMRoteirizado(sql(SQL_UF), texto("MG gastou mais.")),
                consultor=ConsultorFalso(LINHAS_UF), config=config()))

    http, eventos = perguntar(cliente)

    assert http.status_code == 200
    assert http.headers["content-type"].startswith("text/event-stream")
    assert http.headers["cache-control"] == "no-cache"
    assert http.headers["x-accel-buffering"] == "no"
    assert [(nome, dados.get("ferramenta")) for nome, dados in eventos] == [
        ("passo", "consultar_sql"), ("passo", "gerar_grafico"), ("resposta", None)]
    final = Resposta.model_validate(eventos[-1][1])
    assert final.respondida is True
    assert final.sql and final.dados == LINHAS_UF and final.fontes == [FONTE_CEAP]
    assert final.passos == [PassoAgente.model_validate(dados) for _, dados in eventos[:-1]]


def test_h5_agente_da_api_grava_o_jsonl():
    obter_agente.cache_clear()
    try:
        agente = obter_agente()
        assert isinstance(agente.registro, RegistroJSONL)
        assert agente.registro.caminho == Path(settings.agente_log_path)
    finally:
        obter_agente.cache_clear()


# --- Edge cases ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("llm", "consultor", "limites", "passos_falhos", "mensagem"),
    [
        pytest.param(LLMRoteirizado(texto("Não sei.")), ConsultorFalso(), {}, 0, SEM_DADOS,
                     id="sem-consulta"),
        pytest.param(LLMRoteirizado(LLMIndisponivel("fora")), ConsultorFalso(), {}, 0, LLM_FORA,
                     id="llm-fora"),
        pytest.param(LLMRoteirizado(sql(SQL_UF)), ConsultorFalso(BancoIndisponivel("fora")), {},
                     1, BANCO_FORA, id="banco-fora"),
        pytest.param(LLMRoteirizado(*[sql(SQL_UF)] * 3), ConsultorFalso(*[LINHAS_UF] * 3),
                     {"agente_max_passos": 2}, 0, LIMITE_PASSOS, id="limite-de-passos"),
        pytest.param(LLMRoteirizado(*[sql(SQL_PROIBIDO)] * 3), ConsultorFalso(),
                     {"agente_max_correcoes": 2}, 3, CORRECOES_ESGOTADAS, id="correcoes"),
    ],
)
def test_e1_recusas_e_falhas_terminam_com_resposta_nao_respondida(
    cliente, llm, consultor, limites, passos_falhos, mensagem
):
    usar(Agente(llm=llm, consultor=consultor, config=config(**limites)))

    http, eventos = perguntar(cliente)

    assert http.status_code == 200
    nomes = [nome for nome, _ in eventos]
    assert nomes.count("resposta") == 1 and nomes[-1] == "resposta"
    assert set(nomes[:-1]) <= {"passo"}
    passos = [dados for nome, dados in eventos if nome == "passo"]
    assert sum(not p["sucesso"] for p in passos) == passos_falhos
    final = eventos[-1][1]
    assert final["respondida"] is False and final["explicacao"] == mensagem
    assert final["passos"] == passos


def test_e4_uma_unica_instancia_do_agente():
    obter_agente.cache_clear()
    try:
        assert obter_agente() is obter_agente()
    finally:
        obter_agente.cache_clear()


# --- Error cases --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "corpo",
    [{}, {"texto": "oi"}, {"texto": "x" * 501}],
    ids=["sem-texto", "curto", "longo"],
)
def test_x1_corpo_invalido_e_barrado_antes_do_agente(cliente, corpo):
    agente = usar(AgenteRoteirizado())

    http = cliente.post("/perguntar", json=corpo)

    assert http.status_code == 422
    assert not http.headers["content-type"].startswith("text/event-stream")
    assert agente.thread is None


def test_x1_json_malformado_e_barrado(cliente):
    agente = usar(AgenteRoteirizado())

    http = cliente.post("/perguntar", content="{", headers={"content-type": "application/json"})

    assert http.status_code == 422
    assert agente.thread is None


def test_x2_x3_excecao_inesperada_vira_evento_erro(cliente):
    usar(AgenteRoteirizado(fim=RuntimeError("detalhe interno SELECT secreto")))

    http, eventos = perguntar(cliente)

    assert http.status_code == 200
    assert eventos == [("erro", {"mensagem": ERRO_INESPERADO})]
    assert "detalhe interno" not in http.text and "Traceback" not in http.text
