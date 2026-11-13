"""Confere, no banco carregado, que todo SQL de referência do conjunto executa e devolve dados
(STORY-006, RN10). Usa o mesmo caminho do agente: categorias reais, sql_guard e `agente_leitura`.

Uso:
    python -m src.eval.validar_gabarito
    python -m src.eval.validar_gabarito --conjunto caminho/do/conjunto.json

Saída do processo: 0 sem falhas, 1 com falhas ou conjunto inválido, 2 com o banco indisponível
ou sem as categorias.
"""

import argparse
import sys
import time
from collections.abc import Callable
from typing import Protocol

from src.eval.conjunto import (
    CAMINHO_CONJUNTO,
    ConjuntoInvalido,
    ItemAvaliacao,
    carregar_conjunto,
)
from src.tools.consultar_sql import (
    BancoIndisponivel,
    ConsultorSQL,
    ErroExecucaoSQL,
    ResultadoConsulta,
)
from src.tools.sql_guard import SQLInvalido
from src.tools.validar_categorias import validar_categorias

SQL_CATEGORIAS = "SELECT DISTINCT categoria FROM despesas ORDER BY categoria"
BANCO_INDISPONIVEL = (
    "Banco indisponível: suba o Postgres e carregue os dados antes de validar o gabarito."
)
SEM_DADOS = "sem dados"


class Consultor(Protocol):
    def consultar(self, sql: str) -> ResultadoConsulta: ...


def _tem_dados(linhas: list[dict]) -> bool:
    return any(valor is not None for linha in linhas for valor in linha.values())


def validar_gabarito(
    itens: list[ItemAvaliacao],
    consultor: Consultor,
    listar_categorias: Callable[[], list[str]],
    escrever: Callable[[str], None] = print,
) -> int:
    try:
        categorias = listar_categorias()
    except BancoIndisponivel:
        escrever(BANCO_INDISPONIVEL)
        return 2
    except (SQLInvalido, ErroExecucaoSQL) as erro:
        escrever(f"Não foi possível listar as categorias: {erro}")
        return 2

    respondiveis = sorted((i for i in itens if i.respondida), key=lambda i: i.id)
    falhas = 0
    for item in respondiveis:
        inicio = time.perf_counter()
        try:
            validar_categorias(item.sql, categorias)
            linhas = consultor.consultar(item.sql).linhas
        except BancoIndisponivel:
            escrever(BANCO_INDISPONIVEL)
            return 2
        except (SQLInvalido, ErroExecucaoSQL) as erro:
            falhas += 1
            escrever(f"FALHA {item.id}: {erro}")
            continue
        if not _tem_dados(linhas):
            falhas += 1
            escrever(f"FALHA {item.id}: {SEM_DADOS}")
            continue
        escrever(f"OK    {item.id} ({round((time.perf_counter() - inicio) * 1000)} ms)")

    total = len(respondiveis)
    escrever(f"Gabarito: {total - falhas} ok, {falhas} falhas de {total}.")
    return 1 if falhas else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Valida o gabarito do conjunto de avaliação")
    parser.add_argument("--conjunto", default=CAMINHO_CONJUNTO)
    args = parser.parse_args()

    try:
        itens = carregar_conjunto(args.conjunto)
    except ConjuntoInvalido as erro:
        print(erro)
        sys.exit(1)

    consultor = ConsultorSQL()

    def listar_categorias() -> list[str]:
        return [linha["categoria"] for linha in consultor.consultar(SQL_CATEGORIAS).linhas]

    sys.exit(validar_gabarito(itens, consultor, listar_categorias))


if __name__ == "__main__":
    main()
