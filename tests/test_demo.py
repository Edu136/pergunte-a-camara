"""Página da demo (STORY-005) com o cliente da API substituído por um falso."""

import json
from pathlib import Path
from unittest import mock

import pytest
from streamlit.testing.v1 import AppTest

from src.api.cliente import FALHA_GENERICA, Falha, PassoRecebido, RespostaRecebida
from src.schemas import Grafico, PassoAgente, Pergunta, Resposta

PAGINA = str(Path(__file__).resolve().parent.parent / "app" / "streamlit_app.py")
PERGUNTA = "Quanto foi gasto por UF em 2025?"
SQL = "SELECT uf, SUM(valor_liquido) AS total FROM despesas GROUP BY uf LIMIT 200"
CONSULTA = PassoAgente(ferramenta="consultar_sql", descricao="Consulta ao banco de dados",
                       entrada={"sql": SQL}, saida="2 linhas", duracao_ms=1234)
GRAFICO = PassoAgente(ferramenta="gerar_grafico", descricao="Escolha automática do gráfico",
                      saida="barra", duracao_ms=3)
DADOS = [{"uf": "MG", "total": 10.0}, {"uf": "SP", "total": 5.0}]
FONTE = "Câmara dos Deputados — CEAP: https://www.camara.leg.br/cotas"
AVISO = "Verifique na fonte oficial antes de usar estes números."


def resposta(**valores):
    base = {"pergunta": PERGUNTA, "sql": SQL, "dados": DADOS, "explicacao": "MG gastou mais.",
            "fontes": [FONTE], "passos": [CONSULTA, GRAFICO],
            "grafico": Grafico(tipo="barra", eixo_x="uf", eixo_y="total", titulo="Total por UF")}
    return Resposta(**{**base, **valores})


class ClienteFalso:
    def __init__(self, *eventos):
        self.eventos = list(eventos)
        self.chamadas = []

    def __call__(self, texto, *args, **kwargs):
        self.chamadas.append(texto)
        return iter(self.eventos)


@pytest.fixture
def pagina():
    """Roda a página com o cliente falso; devolve (AppTest, falso, executar)."""
    falso = ClienteFalso(PassoRecebido(CONSULTA), PassoRecebido(GRAFICO),
                         RespostaRecebida(resposta()))
    at = AppTest.from_file(PAGINA, default_timeout=30)
    with mock.patch("src.api.cliente.perguntar", falso):
        yield at, falso
    # O AppTest guarda a exceção da página em vez de propagá-la.
    assert not at.exception, [e.message for e in at.exception]


def enviar(at, texto=PERGUNTA):
    at.text_input(key="texto").input(texto)
    at.button[0].click().run()
    return at


def textos(elementos):
    return [e.value for e in elementos]


def figuras(at):
    return [json.loads(e.proto.spec) for e in at.get("plotly_chart")]


# --- Happy path ---------------------------------------------------------------------------

def test_h5_pergunta_de_exemplo_e_enviada_ao_clicar(pagina):
    at, falso = pagina
    at.run()
    primeira = at.pills(key="exemplo").options[0]

    at.pills(key="exemplo").set_value(primeira).run()

    assert falso.chamadas == [primeira]


def test_h6_passos_com_resultado_duracao_e_sql(pagina):
    at, _ = pagina
    at.run()

    enviar(at)

    (status,) = at.status
    linhas = textos(status.markdown)
    assert "✅ Consulta ao banco de dados: 2 linhas (1,2 s)" in linhas
    assert "✅ Escolha automática do gráfico: barra (0,0 s)" in linhas
    assert SQL in textos(status.code)


def test_h3_resposta_com_grafico_de_barras(pagina):
    at, _ = pagina
    at.run()

    enviar(at)

    assert "MG gastou mais." in textos(at.markdown)
    assert [f["data"][0]["type"] for f in figuras(at)] == ["bar", "table"]
    assert textos(at.code).count(SQL) == 2  # no passo e na resposta
    assert any(FONTE in texto for texto in textos(at.markdown))
    assert textos(at.info) == [AVISO]
    assert at.status[0].label == "Concluído"


def test_h4_grafico_tabela_nao_duplica_a_tabela(pagina):
    at, falso = pagina
    grafico = Grafico(tipo="tabela", eixo_x="uf", eixo_y="total", titulo="Resultado da consulta")
    falso.eventos = [RespostaRecebida(resposta(grafico=grafico))]
    at.run()

    enviar(at)

    assert [f["data"][0]["type"] for f in figuras(at)] == ["table"]


# --- Edge cases ---------------------------------------------------------------------------

def test_e2_valor_unico_mostra_so_a_tabela(pagina):
    at, falso = pagina
    falso.eventos = [RespostaRecebida(resposta(grafico=None, dados=[{"total": 15.0}]))]
    at.run()

    enviar(at)

    assert [f["data"][0]["type"] for f in figuras(at)] == ["table"]
    assert "MG gastou mais." in textos(at.markdown)


def test_e3_resposta_nao_respondida_vira_so_aviso(pagina):
    at, falso = pagina
    explicacao = "Não foi possível responder com os dados disponíveis."
    falso.eventos = [RespostaRecebida(Resposta(pergunta=PERGUNTA, explicacao=explicacao,
                                               respondida=False))]
    at.run()

    enviar(at)

    assert textos(at.warning) == [explicacao]
    assert not figuras(at) and not at.code and not at.info
    assert not any("camara.leg.br" in texto for texto in textos(at.markdown))


def test_e4_valores_em_reais_nao_viram_formula(pagina):
    at, falso = pagina
    falso.eventos = [RespostaRecebida(resposta(explicacao="MG gastou R$ 10,00 e SP R$ 20,00."))]
    at.run()

    enviar(at)

    assert r"MG gastou R\$ 10,00 e SP R\$ 20,00." in textos(at.markdown)


def test_e5_interagir_com_a_pagina_nao_refaz_a_pergunta(pagina):
    at, falso = pagina
    at.run()
    enviar(at)

    at.run()

    assert falso.chamadas == [PERGUNTA]
    assert "MG gastou mais." in textos(at.markdown)
    assert [f["data"][0]["type"] for f in figuras(at)] == ["bar", "table"]
    assert "✅ Consulta ao banco de dados: 2 linhas (1,2 s)" in textos(at.status[0].markdown)


def test_e6_perguntas_de_exemplo_neutras_e_validas(pagina):
    at, _ = pagina
    exemplos = at.run().pills(key="exemplo").options
    proibidos = ("absurdo", "abusivo", "suspeito", "irregular", "escandaloso", "desperdício",
                 "exagerado")

    assert 3 <= len(exemplos) <= 5
    for exemplo in exemplos:
        Pergunta(texto=exemplo)
        assert not any(palavra in exemplo.lower() for palavra in proibidos)


# --- Error cases --------------------------------------------------------------------------

def test_x2_pergunta_invalida_e_barrada_na_pagina(pagina):
    at, falso = pagina
    at.run()

    enviar(at, "oi")

    assert textos(at.warning) == ["A pergunta precisa ter entre 5 e 500 caracteres."]
    assert falso.chamadas == []
    assert not at.status


def test_x3_falha_depois_de_um_passo_preserva_o_passo(pagina):
    at, falso = pagina
    falso.eventos = [PassoRecebido(CONSULTA), Falha(FALHA_GENERICA)]
    at.run()

    enviar(at)

    assert textos(at.error) == [FALHA_GENERICA]
    (status,) = at.status
    assert status.label == "Não foi possível concluir"
    assert "✅ Consulta ao banco de dados: 2 linhas (1,2 s)" in textos(status.markdown)
    assert not figuras(at) and not at.info
    assert textos(at.code) == [SQL]  # só o do passo
