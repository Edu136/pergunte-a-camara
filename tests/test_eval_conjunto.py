"""STORY-006: schema e carga do conjunto de avaliação (RN1–RN5), dificuldade (RN7) e vazamento
(RN8). Cenários E1, E2, E5, X1, X2, X3."""

import json

import pytest

from src.eval.conjunto import (
    ConjuntoInvalido,
    carregar_conjunto,
    classificar_dificuldade,
    normalizar,
    perguntas_exemplo_da_demo,
    vazamentos,
)

SQL_TOTAL = "SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024"
SQL_RANKING = (
    "SELECT categoria, SUM(valor_liquido) AS total FROM despesas "
    "GROUP BY categoria ORDER BY total DESC LIMIT 5"
)


def _item(**campos):
    base = {
        "id": "F01",
        "categoria": "facil",
        "pergunta": "Quanto foi gasto no total em 2024?",
        "respondida": True,
        "sql": SQL_TOTAL,
    }
    return base | campos


def _recusa(id_, categoria):
    return {
        "id": id_,
        "categoria": categoria,
        "pergunta": "Pergunta que o agente deveria recusar.",
        "respondida": False,
        "sql": None,
    }


def _gravar(tmp_path, conteudo):
    caminho = tmp_path / "conjunto.json"
    texto = conteudo if isinstance(conteudo, str) else json.dumps(conteudo, ensure_ascii=False)
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def _erro(tmp_path, itens):
    with pytest.raises(ConjuntoInvalido) as erro:
        carregar_conjunto(_gravar(tmp_path, itens))
    return str(erro.value)


# --- carga válida ------------------------------------------------------------------------------


def test_carrega_itens_validos(tmp_path):
    itens = [
        _item(),
        _item(id="M01", categoria="media", sql=SQL_RANKING, ordem_importa=True, nota="ranking"),
        _recusa("O01", "opiniao"),
        _recusa("X01", "fora_do_escopo"),
        _recusa("I01", "injection"),
    ]
    conjunto = carregar_conjunto(_gravar(tmp_path, itens))

    assert [item.id for item in conjunto] == ["F01", "M01", "O01", "X01", "I01"]
    assert conjunto[0].ordem_importa is False
    assert conjunto[1].ordem_importa is True and conjunto[1].nota == "ranking"
    assert conjunto[2].sql is None and conjunto[2].respondida is False


# --- E5 ----------------------------------------------------------------------------------------


def test_e5_ordem_importa_sem_order_by_e_invalido(tmp_path):
    item = _item(id="M01", categoria="media",
                 sql="SELECT uf, SUM(valor_liquido) FROM despesas GROUP BY uf", ordem_importa=True)
    mensagem = _erro(tmp_path, [item])
    assert "Item M01: " in mensagem and "ORDER BY" in mensagem


# --- X1 ----------------------------------------------------------------------------------------


def test_x1_arquivo_ausente(tmp_path):
    with pytest.raises(ConjuntoInvalido, match="Arquivo do conjunto não encontrado"):
        carregar_conjunto(tmp_path / "nao_existe.json")


@pytest.mark.parametrize("conteudo", ["[{", '{"id": "F01"}'], ids=["malformado", "raiz-objeto"])
def test_x1_json_invalido(tmp_path, conteudo):
    with pytest.raises(ConjuntoInvalido, match="Conjunto de avaliação com JSON inválido"):
        carregar_conjunto(_gravar(tmp_path, conteudo))


# --- X2 ----------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("item", "id_"),
    [
        (_item(pergunta="abc"), "F01"),
        (_item(categoria="trivial"), "F01"),
        (_item(esperado="x"), "F01"),
        (_item(id="M01"), "M01"),
        (_item(sql=None), "F01"),
        (_item(respondida=False), "F01"),
        (_recusa("O01", "opiniao") | {"sql": SQL_TOTAL}, "O01"),
        (_recusa("I01", "injection") | {"respondida": True}, "I01"),
        (_recusa("O01", "opiniao") | {"ordem_importa": True}, "O01"),
    ],
    ids=[
        "pergunta-curta", "categoria-desconhecida", "campo-desconhecido", "prefixo-errado",
        "respondivel-sem-sql", "respondivel-recusada", "opiniao-com-sql",
        "injection-respondida", "recusa-com-ordem",
    ],
)
def test_x2_item_invalido_aponta_o_id(tmp_path, item, id_):
    assert f"Item {id_}: " in _erro(tmp_path, [item])


def test_x2_item_sem_id_legivel_aponta_a_posicao(tmp_path):
    assert "Item na posição 2: " in _erro(tmp_path, [_item(), {"pergunta": "sem id nenhum"}])


def test_x2_sql_com_erro_de_sintaxe_e_invalido(tmp_path):
    item = _item(id="M01", categoria="media", sql="SELECT FROM WHERE (", ordem_importa=True)
    assert "Item M01: " in _erro(tmp_path, [item])


# --- X3 ----------------------------------------------------------------------------------------


def test_x3_ids_repetidos(tmp_path):
    mensagem = _erro(tmp_path, [_item(), _item(pergunta="Outra pergunta qualquer?")])
    assert "Ids repetidos: F01" in mensagem


# --- E2 (RN7) ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sql", "esperado"),
    [
        ("SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024", "facil"),
        ("SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024 AND uf = 'MG'", "facil"),
        ("SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024 AND uf = 'MG' AND mes = 1",
         "media"),
        ("SELECT uf, SUM(valor_liquido) FROM despesas GROUP BY uf", "media"),
        ("SELECT fornecedor FROM despesas ORDER BY valor_liquido DESC LIMIT 5", "media"),
        ("SELECT d.nome FROM despesas e JOIN deputados d ON d.id = e.deputado_id", "dificil"),
        ("WITH t AS (SELECT 1 AS x) SELECT x FROM t", "dificil"),
        ("SELECT uf, SUM(valor_liquido) / (SELECT SUM(valor_liquido) FROM despesas) "
         "FROM despesas GROUP BY uf", "dificil"),
        ("SELECT uf, RANK() OVER (ORDER BY SUM(valor_liquido)) FROM despesas GROUP BY uf",
         "dificil"),
        ("SELECT COUNT(*) FROM despesas WHERE deputado_id IN (SELECT id FROM deputados)",
         "dificil"),
    ],
)
def test_e2_classificacao_de_dificuldade(sql, esperado):
    assert classificar_dificuldade(sql) == esperado


# --- E1 (RN8) ----------------------------------------------------------------------------------


def test_normalizar_tira_acento_caixa_e_pontuacao():
    assert normalizar("  Quanto foi GASTO, por UF em 2025?! ") == "quanto foi gasto por uf em 2025"
    assert normalizar("Divulgação  da  atividade") == "divulgacao da atividade"


def test_e1_vazamento_apesar_de_acento_caixa_e_pontuacao():
    perguntas = ["QUANTO foi gasto por uf em 2025", "Qual a média mensal em 2024?"]
    assert vazamentos(perguntas, ["Quanto foi gasto por UF em 2025?"]) == [perguntas[0]]


def test_vazamento_dentro_de_um_texto_maior():
    prompt = "Exemplo: Quanto foi gasto por UF em 2025? Use valor_liquido."
    assert vazamentos(["quanto foi gasto por uf em 2025"], [prompt]) != []


def test_sem_vazamento_por_pedaco_de_palavra():
    assert vazamentos(["gasto em 2024"], ["Total gastos em 20245"]) == []


def test_perguntas_exemplo_lidas_da_demo_sem_executar_a_pagina():
    exemplos = perguntas_exemplo_da_demo()
    assert 3 <= len(exemplos) <= 5
    assert all(isinstance(e, str) and e for e in exemplos)


# --- revisão: gabarito passa pelo sql_guard já na carga (RN6) ----------------------------------


@pytest.mark.parametrize(
    ("sql", "trecho"),
    [
        ("DELETE FROM despesas", "SELECT"),
        ("SELECT 1; SELECT 2", "exatamente um comando"),
        ("SELECT * FROM pg_user", "Tabelas não permitidas"),
    ],
    ids=["escrita", "dois-comandos", "tabela-proibida"],
)
def test_gabarito_barrado_pelo_sql_guard_na_carga(tmp_path, sql, trecho):
    mensagem = _erro(tmp_path, [_item(sql=sql)])
    assert "Item F01: " in mensagem and trecho in mensagem


def test_x1_arquivo_fora_de_utf8_e_json_invalido(tmp_path):
    caminho = tmp_path / "conjunto.json"
    caminho.write_bytes(b'[{"id": "F01"}]\xff')
    with pytest.raises(ConjuntoInvalido, match="Conjunto de avaliação com JSON inválido"):
        carregar_conjunto(caminho)
