"""STORY-006: o conjunto versionado em experiments/ (cenários H1, H2, H3, H4, H6)."""

from collections import Counter

import pytest
import sqlglot
from sqlglot import exp

from src.agent.prompts import PROMPT_SISTEMA
from src.eval.conjunto import (
    PREFIXOS,
    carregar_conjunto,
    classificar_dificuldade,
    perguntas_exemplo_da_demo,
    vazamentos,
)
from src.tools.sql_guard import validar_sql

ITENS_POR_CATEGORIA = 10
CONJUNTO = carregar_conjunto()
RESPONDIVEIS = [item for item in CONJUNTO if item.respondida]


def test_h1_conjunto_valido_e_balanceado():
    assert Counter(item.categoria for item in CONJUNTO) == {
        categoria: ITENS_POR_CATEGORIA for categoria in PREFIXOS
    }


@pytest.mark.parametrize("item", RESPONDIVEIS, ids=lambda i: i.id)
def test_h2_gabarito_passa_no_sql_guard(item):
    validar_sql(item.sql)


@pytest.mark.parametrize("item", RESPONDIVEIS, ids=lambda i: i.id)
def test_h3_categoria_bate_com_a_dificuldade_do_sql(item):
    assert classificar_dificuldade(item.sql) == item.categoria


@pytest.mark.parametrize("item", RESPONDIVEIS, ids=lambda i: i.id)
def test_rn6_limit_so_em_ranking(item):
    consulta = sqlglot.parse_one(item.sql, read="postgres")
    if consulta.args.get("limit") is not None:
        assert item.ordem_importa, "LIMIT no gabarito só em ranking (ordem_importa)"


def test_h4_nenhuma_pergunta_vaza_para_a_demo_ou_o_prompt():
    perguntas = [item.pergunta for item in CONJUNTO]
    referencias = [*perguntas_exemplo_da_demo(), PROMPT_SISTEMA]
    assert vazamentos(perguntas, referencias) == []


def _casos_story_005():
    return [item for item in RESPONDIVEIS if item.nota and "STORY-005" in item.nota]


def test_h6_ranking_de_categorias_da_story_005():
    rankings = []
    for item in _casos_story_005():
        consulta = sqlglot.parse_one(item.sql, read="postgres")
        limite = consulta.args.get("limit")
        agrupa_categoria = any(
            isinstance(g, exp.Column) and g.name == "categoria"
            for g in (consulta.args.get("group").expressions if consulta.args.get("group") else [])
        )
        if item.ordem_importa and limite is not None and agrupa_categoria:
            rankings.append(int(limite.expression.this))
    assert rankings and all(n >= 5 for n in rankings)


def test_h6_agrupamento_por_categoria_em_2025_da_story_005():
    def agrupa_categoria_em_2025(sql):
        consulta = sqlglot.parse_one(sql, read="postgres")
        grupo = consulta.args.get("group")
        filtro = consulta.args.get("where")
        return (
            grupo is not None
            and any(isinstance(g, exp.Column) and g.name == "categoria" for g in grupo.expressions)
            and filtro is not None
            and "2025" in filtro.sql()
        )

    assert any(agrupa_categoria_em_2025(item.sql) for item in _casos_story_005())
