import pytest

from src.tools.grafico import escolher_grafico


def _escolher(dados, max_barras=20):
    return escolher_grafico(dados, max_barras=max_barras)


def test_h1_evolucao_mensal_vira_linha():
    grafico = _escolher([{"mes": 1, "total": 10.0}, {"mes": 2, "total": 12.5}])

    assert (grafico.tipo, grafico.eixo_x, grafico.eixo_y) == ("linha", "mes", "total")
    assert grafico.titulo == "Total por Mês"


def test_h2_comparacao_por_uf_vira_barra():
    grafico = _escolher([{"uf": "MG", "valor_liquido": 10.0}, {"uf": "SP", "valor_liquido": 5.0}])

    assert (grafico.tipo, grafico.eixo_x, grafico.eixo_y) == ("barra", "uf", "valor_liquido")
    assert grafico.titulo == "Valor líquido por UF"


@pytest.mark.parametrize("dados", [[{"total": 2646274.41}], []])
def test_e1_e2_valor_unico_ou_sem_linhas_nao_vira_grafico(dados):
    assert _escolher(dados) is None


def test_e3_data_iso_e_tempo():
    grafico = _escolher([{"data_emissao": "2025-01-02", "valor_liquido": 1.0},
                         {"data_emissao": "2025-01-03", "valor_liquido": 2.0}])

    assert (grafico.tipo, grafico.eixo_x) == ("linha", "data_emissao")


def test_e4_ano_e_mes_de_um_unico_ano_vira_linha_por_mes():
    grafico = _escolher([{"ano": 2025, "mes": 1, "total": 1.0},
                         {"ano": 2025, "mes": 2, "total": 2.0}])

    assert (grafico.tipo, grafico.eixo_x, grafico.eixo_y) == ("linha", "mes", "total")


def test_e4_ano_e_mes_de_varios_anos_vira_tabela():
    grafico = _escolher([{"ano": 2024, "mes": 12, "total": 1.0},
                         {"ano": 2025, "mes": 1, "total": 2.0}])

    assert grafico.tipo == "tabela"


def test_e5_categorias_demais_viram_tabela():
    dados = [{"uf": uf, "total": 1.0} for uf in ["MG", "SP", "RJ", "BA"]]

    assert _escolher(dados, max_barras=3).tipo == "tabela"
    assert _escolher(dados, max_barras=4).tipo == "barra"


def test_e6_varias_medidas_usam_a_primeira():
    grafico = _escolher([{"uf": "MG", "total": 10.0, "quantidade": 3},
                         {"uf": "SP", "total": 5.0, "quantidade": 2}])

    assert (grafico.tipo, grafico.eixo_y) == ("barra", "total")


def test_e7_id_e_dimensao():
    grafico = _escolher([{"deputado_id": 1, "total": 5.0}, {"deputado_id": 2, "total": 3.0}])

    assert (grafico.tipo, grafico.eixo_x, grafico.eixo_y) == ("barra", "deputado_id", "total")


def test_e7_booleano_nao_e_medida():
    assert _escolher([{"uf": "MG", "ativo": True}, {"uf": "SP", "ativo": False}]).tipo == "tabela"


def test_e9_rotulos_de_colunas_desconhecidas():
    grafico = _escolher([{"nome_parlamentar": "A", "soma_gastos": 1.0},
                         {"nome_parlamentar": "B", "soma_gastos": 2.0}])

    assert grafico.titulo == "Soma gastos por Nome parlamentar"


def test_x1_sem_medida_vira_tabela_com_eixos_informativos():
    grafico = _escolher([{"uf": "MG", "partido": "X"}, {"uf": "SP", "partido": "Y"}])

    assert (grafico.tipo, grafico.eixo_x, grafico.eixo_y) == ("tabela", "uf", "uf")
    assert grafico.titulo == "Resultado da consulta"


def test_x3_nulos_na_medida():
    grafico = _escolher([{"uf": "MG", "total": None}, {"uf": "SP", "total": 5.0}])

    assert (grafico.tipo, grafico.eixo_y) == ("barra", "total")


def test_varias_linhas_so_com_medidas_vira_tabela():
    assert _escolher([{"total": 1.0}, {"total": 2.0}]).tipo == "tabela"


def test_tempo_com_uma_linha_so_vira_tabela():
    assert _escolher([{"mes": 1, "total": 1.0}]).tipo == "tabela"


def test_pizza_nunca_e_escolhida():
    casos = [
        [{"categoria": "A", "total": 70.0}, {"categoria": "B", "total": 30.0}],
        [{"mes": 1, "total": 1.0}, {"mes": 2, "total": 2.0}],
        [{"uf": "MG", "partido": "X"}],
    ]
    assert all(_escolher(dados).tipo != "pizza" for dados in casos)
