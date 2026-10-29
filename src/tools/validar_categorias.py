"""Confere se os textos de categoria citados no SQL existem de verdade (STORY-002).

O modelo costuma "normalizar" os textos oficiais da Câmara (ex.: tira o ponto de
"COMBUSTÍVEIS E LUBRIFICANTES."), e o filtro passa a não encontrar nada. Aqui a consulta é
barrada antes do banco, com sugestões, para a autocorreção do agente resolver.
"""

import difflib

import sqlglot
from sqlglot import exp

from src.tools.sql_guard import SQLInvalido

COLUNA = "categoria"
MAX_SUGESTOES = 3


class CategoriaInexistente(SQLInvalido):
    pass


def _eh_coluna_categoria(no: exp.Expression) -> bool:
    return isinstance(no, exp.Column) and no.name.lower() == COLUNA


def _textos_comparados(consulta: exp.Expression) -> list[str]:
    textos = []
    for comparacao in consulta.find_all(exp.EQ, exp.NEQ):
        lados = (comparacao.this, comparacao.expression)
        for coluna, valor in (lados, lados[::-1]):
            if _eh_coluna_categoria(coluna) and isinstance(valor, exp.Literal) and valor.is_string:
                textos.append(valor.this)
    for lista in consulta.find_all(exp.In):
        if _eh_coluna_categoria(lista.this):
            textos += [v.this for v in lista.expressions
                       if isinstance(v, exp.Literal) and v.is_string]
    return textos


def _sugestoes(texto: str, categorias: list[str]) -> list[str]:
    """Categorias que contêm o texto (ex.: "combustíveis") e, depois, as mais parecidas."""
    por_maiuscula = {c.upper(): c for c in categorias}
    alvo = texto.upper().strip()
    contem = [c for m, c in por_maiuscula.items() if alvo and alvo in m]
    proximas = difflib.get_close_matches(alvo, por_maiuscula, n=MAX_SUGESTOES)
    parecidas = [por_maiuscula[p] for p in proximas]
    return list(dict.fromkeys(contem + parecidas))[:MAX_SUGESTOES]


def validar_categorias(sql: str, categorias: list[str]) -> None:
    """Lança CategoriaInexistente se o SQL compara `categoria` com um texto que não existe."""
    if not categorias:
        return
    try:
        consulta = sqlglot.parse_one(sql, read="postgres")
    except sqlglot.errors.ParseError:
        return  # o sql_guard rejeita com a mensagem de sintaxe

    existentes = set(categorias)
    for texto in _textos_comparados(consulta):
        if texto in existentes:
            continue
        sugestoes = _sugestoes(texto, categorias)
        if sugestoes:
            opcoes = ", ".join(f"'{s}'" for s in sugestoes)
            raise CategoriaInexistente(
                f"Categoria '{texto}' não existe. Use o texto exato; você quis dizer {opcoes}?"
            )
        raise CategoriaInexistente(
            f"Categoria '{texto}' não existe. Use exatamente uma das categorias listadas no prompt."
        )
