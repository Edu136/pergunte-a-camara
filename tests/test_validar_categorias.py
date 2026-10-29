import pytest

from src.tools.sql_guard import SQLInvalido
from src.tools.validar_categorias import CategoriaInexistente, validar_categorias

CATEGORIAS = ["COMBUSTÍVEIS E LUBRIFICANTES.", "TELEFONIA", "SERVIÇOS POSTAIS"]
BASE = "SELECT SUM(valor_liquido) FROM despesas d WHERE "


def test_h1_categoria_exata_executa():
    validar_categorias(BASE + "categoria = 'COMBUSTÍVEIS E LUBRIFICANTES.'", CATEGORIAS)


def test_categoria_quase_igual_sugere_a_oficial():
    with pytest.raises(CategoriaInexistente) as erro:
        validar_categorias(BASE + "categoria = 'COMBUSTÍVEIS E LUBRIFICANTES'", CATEGORIAS)
    assert "'COMBUSTÍVEIS E LUBRIFICANTES.'" in str(erro.value)


def test_erro_e_um_sql_invalido_corrigivel():
    assert issubclass(CategoriaInexistente, SQLInvalido)


@pytest.mark.parametrize("filtro, invalido", [
    ("d.categoria IN ('TELEFONIA', 'CORREIOS')", "CORREIOS"),
    ("categoria <> 'TELEFONE'", "TELEFONE"),
    ("categoria != 'TELEFONE'", "TELEFONE"),
    ("'TELEFONE' = categoria", "TELEFONE"),
])
def test_e1_in_diferente_prefixo_e_lado_invertido(filtro, invalido):
    with pytest.raises(CategoriaInexistente, match=invalido):
        validar_categorias(BASE + filtro, CATEGORIAS)


def test_e2_diferenca_so_de_maiusculas():
    with pytest.raises(CategoriaInexistente, match="'TELEFONIA'"):
        validar_categorias(BASE + "categoria = 'telefonia'", CATEGORIAS)


def test_e3_sem_lista_nao_valida():
    validar_categorias(BASE + "categoria = 'QUALQUER'", [])


@pytest.mark.parametrize("filtro", ["categoria ILIKE 'telef%'", "categoria LIKE 'TELEF%'",
                                    "categoria = subcategoria"])
def test_e4_like_e_comparacao_entre_colunas_nao_sao_validados(filtro):
    validar_categorias(BASE + filtro, CATEGORIAS)


def test_x1_sem_nada_parecido():
    with pytest.raises(CategoriaInexistente, match="categorias listadas"):
        validar_categorias(BASE + "categoria = 'XYZ'", CATEGORIAS)


def test_sql_que_nao_compila_fica_para_o_guard():
    validar_categorias("SELECT FROM WHERE (", CATEGORIAS)


def test_e6_texto_contido_numa_categoria_vira_sugestao():
    with pytest.raises(CategoriaInexistente, match="'COMBUSTÍVEIS E LUBRIFICANTES.'"):
        validar_categorias(BASE + "categoria = 'combustíveis'", CATEGORIAS)
