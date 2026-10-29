from src.schemas import Grafico
from src.tools.grafico import COR_SERIE, montar_figura

DADOS_UF = [{"uf": "MG", "valor_liquido": 10.0}, {"uf": "SP", "valor_liquido": 5.0}]
BARRA = Grafico(tipo="barra", eixo_x="uf", eixo_y="valor_liquido", titulo="Valor líquido por UF")


def test_h4_figura_de_barras_em_reais_e_pt_br():
    figura = montar_figura(BARRA, DADOS_UF)

    (serie,) = figura.data
    assert serie.type == "bar"
    assert list(serie.x) == ["MG", "SP"] and list(serie.y) == [10.0, 5.0]
    assert serie.marker.color == COR_SERIE
    assert figura.layout.title.text == "Valor líquido por UF"
    assert figura.layout.yaxis.tickprefix == "R$ "
    assert figura.layout.separators == ",."
    assert "R$" in serie.hovertemplate
    assert figura.layout.showlegend is False


def test_h5_figura_de_linha():
    grafico = Grafico(tipo="linha", eixo_x="mes", eixo_y="total", titulo="Total por Mês")

    figura = montar_figura(grafico, [{"mes": 1, "total": 1.0}, {"mes": 2, "total": 2.0}])

    (serie,) = figura.data
    assert serie.type == "scatter" and serie.mode == "lines+markers"
    assert list(serie.x) == [1, 2]
    assert serie.line.width == 2 and serie.marker.size == 8


def test_e8_contagem_sem_reais():
    grafico = Grafico(tipo="barra", eixo_x="uf", eixo_y="quantidade", titulo="Quantidade por UF")

    figura = montar_figura(grafico, [{"uf": "MG", "quantidade": 3}, {"uf": "SP", "quantidade": 2}])

    assert not figura.layout.yaxis.tickprefix
    assert "R$" not in figura.data[0].hovertemplate


def test_e10_figura_de_tabela_com_todas_as_colunas_e_linhas():
    dados = [{"uf": "MG", "partido": "X", "valor_liquido": 1.5},
             {"uf": "SP", "partido": "Y", "valor_liquido": 2.0}]
    grafico = Grafico(tipo="tabela", eixo_x="uf", eixo_y="valor_liquido",
                      titulo="Resultado da consulta")

    figura = montar_figura(grafico, dados)

    (tabela,) = figura.data
    assert tabela.type == "table"
    assert list(tabela.header.values) == ["UF", "Partido", "Valor líquido"]
    assert [list(coluna) for coluna in tabela.cells.values] == [
        ["MG", "SP"], ["X", "Y"], ["R$ 1,50", "R$ 2,00"]]


def test_e11_eixo_de_valores_comeca_em_zero_para_nao_exagerar_variacoes():
    grafico = Grafico(tipo="linha", eixo_x="mes", eixo_y="total", titulo="Total por Mês")

    figura = montar_figura(grafico, [{"mes": 1, "total": 1.4e6}, {"mes": 2, "total": 2.0e6}])

    assert figura.layout.yaxis.rangemode == "tozero"


def test_e12_meses_aparecem_por_extenso_abreviado():
    grafico = Grafico(tipo="linha", eixo_x="mes", eixo_y="total", titulo="Total por Mês")

    figura = montar_figura(grafico, [{"mes": 1, "total": 1.0}, {"mes": 2, "total": 2.0}])

    assert list(figura.layout.xaxis.tickvals) == list(range(1, 13))
    assert list(figura.layout.xaxis.ticktext)[:3] == ["jan", "fev", "mar"]


def test_x4_barras_tratam_o_eixo_x_como_categoria_mesmo_numerico():
    grafico = Grafico(tipo="barra", eixo_x="deputado_id", eixo_y="total",
                      titulo="Total por Deputado id")

    figura = montar_figura(grafico, [{"deputado_id": 220593, "total": 5.0},
                                     {"deputado_id": 74000, "total": 3.0}])

    assert figura.layout.xaxis.type == "category"


def test_x5_ano_no_eixo_x_e_inteiro_sem_separador():
    grafico = Grafico(tipo="linha", eixo_x="ano", eixo_y="total", titulo="Total por Ano")

    figura = montar_figura(grafico, [{"ano": 2024, "total": 1.0}, {"ano": 2025, "total": 2.0}])

    assert figura.layout.xaxis.dtick == 1 and figura.layout.xaxis.tickformat == "d"


def test_x6_tabela_formata_valores_em_reais_e_contagens_como_inteiros():
    dados = [{"uf": "SP", "valor_liquido": 6619024.49, "quantidade": 1200}]
    grafico = Grafico(tipo="tabela", eixo_x="uf", eixo_y="valor_liquido",
                      titulo="Resultado da consulta")

    figura = montar_figura(grafico, dados)

    # Confere o texto exibido: o go.Table ignora layout.separators.
    colunas = [list(coluna) for coluna in figura.data[0].cells.values]
    assert colunas == [["SP"], ["R$ 6.619.024,49"], ["1.200"]]
