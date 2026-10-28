"""Primeira camada de proteção: valida o SQL gerado pelo LLM antes de executá-lo.

Regras (spec 00, P3):
- apenas um comando, e ele precisa ser SELECT;
- apenas tabelas permitidas;
- nenhuma escrita ou bloqueio escondido no SELECT (CTE com DELETE/UPDATE, INTO, FOR UPDATE);
- nenhuma função de sistema (pg_*, dblink*, lo_*, set_config, current_setting);
- sempre com LIMIT (adicionado ou reduzido até o máximo configurado).
"""

import sqlglot
from sqlglot import exp

TABELAS_PERMITIDAS = {"deputados", "despesas"}
PREFIXOS_FUNCOES_PROIBIDAS = ("pg_", "dblink", "lo_", "set_config", "current_setting")
NOS_PROIBIDOS = (
    exp.Insert, exp.Update, exp.Delete, exp.Merge, exp.Create, exp.Drop, exp.Command,
    exp.Into, exp.Lock,
)


class SQLInvalido(ValueError):
    pass


def validar_sql(sql: str, limite_maximo: int = 200) -> str:
    try:
        comandos = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as erro:
        raise SQLInvalido(f"SQL com erro de sintaxe: {erro}") from erro

    comandos = [c for c in comandos if c is not None]
    if len(comandos) != 1:
        raise SQLInvalido("Envie exatamente um comando SQL.")

    consulta = comandos[0]
    if not isinstance(consulta, exp.Select):
        raise SQLInvalido("Apenas consultas SELECT são permitidas.")

    no_proibido = consulta.find(*NOS_PROIBIDOS)
    if no_proibido is not None:
        raise SQLInvalido(
            f"Apenas leitura é permitida: a consulta contém {no_proibido.key.upper()}."
        )

    for funcao in consulta.find_all(exp.Func):
        nome = (funcao.name if isinstance(funcao, exp.Anonymous) else funcao.sql_name()).lower()
        if nome.startswith(PREFIXOS_FUNCOES_PROIBIDAS):
            raise SQLInvalido(f"Função não permitida: {nome}")

    nomes_cte = {cte.alias for cte in consulta.find_all(exp.CTE)}
    tabelas = {t.name for t in consulta.find_all(exp.Table)} - nomes_cte
    proibidas = tabelas - TABELAS_PERMITIDAS
    if proibidas:
        raise SQLInvalido(f"Tabelas não permitidas: {', '.join(sorted(proibidas))}")

    limite = consulta.args.get("limit")
    if limite is None:
        consulta = consulta.limit(limite_maximo)
    else:
        valor = limite.expression
        if not isinstance(valor, exp.Literal) or int(valor.this) > limite_maximo:
            consulta = consulta.limit(limite_maximo)

    return consulta.sql(dialect="postgres")
