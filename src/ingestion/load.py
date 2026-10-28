"""Carga no Postgres. Recarregar um ano é idempotente: apaga as despesas dele e insere de novo."""

import logging

import pandas as pd
import psycopg

from src.ingestion.transform import COLUNAS_DEPUTADOS, COLUNAS_DESPESAS

log = logging.getLogger(__name__)

SQL_UPSERT_DEPUTADO = """
INSERT INTO deputados (id, nome, partido, uf, legislatura, url_foto)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (id) DO UPDATE SET
    nome = EXCLUDED.nome,
    partido = EXCLUDED.partido,
    uf = EXCLUDED.uf,
    legislatura = GREATEST(deputados.legislatura, EXCLUDED.legislatura),
    url_foto = COALESCE(EXCLUDED.url_foto, deputados.url_foto)
"""


def _linhas(df: pd.DataFrame, colunas: list[str]):
    """Converte o DataFrame em tuplas trocando NA/NaN do pandas por None."""
    limpo = df[colunas].astype(object).where(df[colunas].notna(), None)
    return limpo.itertuples(index=False, name=None)


def carregar(
    conexao: psycopg.Connection,
    deputados: pd.DataFrame,
    despesas: pd.DataFrame,
    fotos: dict[int, str] | None = None,
) -> None:
    fotos = fotos or {}
    deputados = deputados.assign(url_foto=deputados["id"].map(lambda i: fotos.get(int(i))))
    anos = sorted(int(a) for a in despesas["ano"].dropna().unique())

    with conexao.transaction(), conexao.cursor() as cursor:
        cursor.executemany(SQL_UPSERT_DEPUTADO, list(_linhas(deputados, [*COLUNAS_DEPUTADOS,
                                                                          "url_foto"])))
        log.info("Deputados inseridos/atualizados: %d", len(deputados))

        cursor.execute("DELETE FROM despesas WHERE ano = ANY(%s)", (anos,))
        log.info("Despesas antigas removidas dos anos %s: %d", anos, cursor.rowcount)

        colunas = ", ".join(COLUNAS_DESPESAS)
        with cursor.copy(f"COPY despesas ({colunas}) FROM STDIN") as copia:
            for linha in _linhas(despesas, COLUNAS_DESPESAS):
                copia.write_row(linha)
        log.info("Despesas carregadas: %d", len(despesas))
