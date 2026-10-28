"""Ferramenta consultar_sql: valida o SQL (1ª camada) e executa com o usuário somente leitura
(2ª camada), em transação READ ONLY e com timeout. Regras em specs/STORY-001/spec.bdd.md.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import psycopg

from src.config import settings
from src.tools.sql_guard import validar_sql

log = logging.getLogger(__name__)


class ErroExecucaoSQL(RuntimeError):
    """Erro da consulta (sintaxe, coluna, timeout): o modelo pode corrigir o SQL."""


class BancoIndisponivel(RuntimeError):
    """Falha de conexão: corrigir o SQL não adianta. A mensagem não expõe host nem porta."""


@dataclass
class ResultadoConsulta:
    sql: str
    linhas: list[dict[str, Any]]


def conectar_leitura() -> psycopg.Connection:
    return psycopg.connect(settings.database_url_leitura)


def _serializar(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, date | datetime):
        return valor.isoformat()
    return valor


class ConsultorSQL:
    def __init__(
        self,
        conectar: Callable[[], psycopg.Connection] = conectar_leitura,
        timeout_ms: int = settings.sql_timeout_ms,
        limite_linhas: int = settings.sql_limite_linhas,
    ):
        self.conectar = conectar
        self.timeout_ms = int(timeout_ms)
        self.limite_linhas = limite_linhas

    def consultar(self, sql: str) -> ResultadoConsulta:
        """Valida e executa. Lança SQLInvalido (guard) ou ErroExecucaoSQL (banco)."""
        sql_validado = validar_sql(sql, self.limite_linhas)
        try:
            with self.conectar() as conexao, conexao.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute(f"SET LOCAL statement_timeout = {self.timeout_ms}")
                cursor.execute(sql_validado)
                colunas = [coluna.name for coluna in cursor.description]
                linhas = [
                    {nome: _serializar(valor) for nome, valor in zip(colunas, linha, strict=True)}
                    for linha in cursor.fetchall()
                ]
        except psycopg.errors.QueryCanceled as erro:
            raise ErroExecucaoSQL(
                f"A consulta excedeu o tempo limite de {self.timeout_ms} ms: "
                "filtre ou agregue os dados para reduzir o volume."
            ) from erro
        except psycopg.OperationalError as erro:
            log.warning("Banco indisponível: %s", erro)
            raise BancoIndisponivel("O banco de dados está indisponível no momento.") from erro
        except psycopg.Error as erro:
            raise ErroExecucaoSQL(f"Erro no banco: {str(erro).strip()}") from erro
        return ResultadoConsulta(sql=sql_validado, linhas=linhas)
