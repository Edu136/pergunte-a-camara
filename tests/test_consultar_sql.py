from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import psycopg
import pytest

from src.tools.consultar_sql import ConsultorSQL, ErroExecucaoSQL
from src.tools.sql_guard import SQLInvalido


class CursorFalso:
    def __init__(self, conexao):
        self.conexao = conexao
        self.description = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, *args):
        self.conexao.comandos.append(sql)
        if sql.startswith("SET"):
            return
        if self.conexao.erro:
            raise self.conexao.erro
        self.description = [SimpleNamespace(name=nome) for nome in self.conexao.colunas]

    def fetchall(self):
        return self.conexao.linhas


class ConexaoFalsa:
    def __init__(self, colunas=(), linhas=(), erro=None):
        self.colunas, self.linhas, self.erro = list(colunas), list(linhas), erro
        self.comandos = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self):
        return CursorFalso(self)


def _consultor(conexao, timeout_ms=5000):
    return ConsultorSQL(conectar=lambda: conexao, timeout_ms=timeout_ms, limite_linhas=200)


def test_executa_com_guard_somente_leitura_e_timeout():
    conexao = ConexaoFalsa(colunas=["uf"], linhas=[("MG",)])

    resultado = _consultor(conexao, timeout_ms=3000).consultar("SELECT uf FROM despesas")

    assert conexao.comandos[0] == "SET TRANSACTION READ ONLY"
    assert conexao.comandos[1] == "SET LOCAL statement_timeout = 3000"
    assert "LIMIT 200" in conexao.comandos[2]
    assert resultado.sql == conexao.comandos[2]
    assert resultado.linhas == [{"uf": "MG"}]


def test_valores_do_banco_sao_serializaveis():
    conexao = ConexaoFalsa(
        colunas=["total", "data"], linhas=[(Decimal("10.50"), date(2025, 1, 31))]
    )

    resultado = _consultor(conexao).consultar("SELECT 1 AS total, 2 AS data FROM despesas")

    assert resultado.linhas == [{"total": 10.5, "data": "2025-01-31"}]


def test_sql_rejeitado_pelo_guard_nao_chega_ao_banco():
    conexao = ConexaoFalsa()

    with pytest.raises(SQLInvalido):
        _consultor(conexao).consultar("DROP TABLE despesas")
    assert conexao.comandos == []


def test_timeout_do_banco_orienta_filtrar_ou_agregar():
    conexao = ConexaoFalsa(erro=psycopg.errors.QueryCanceled("canceling statement"))

    with pytest.raises(ErroExecucaoSQL, match="tempo limite.*filtre ou agregue"):
        _consultor(conexao).consultar("SELECT * FROM despesas")


def test_erro_do_banco_vira_erro_de_execucao_com_a_mensagem():
    erro = psycopg.errors.UndefinedColumn('column "valor" does not exist')
    conexao = ConexaoFalsa(erro=erro)

    with pytest.raises(ErroExecucaoSQL, match='column "valor" does not exist'):
        _consultor(conexao).consultar("SELECT valor FROM despesas")


def test_falha_de_conexao_vira_banco_indisponivel_sem_detalhes_internos():
    from src.tools.consultar_sql import BancoIndisponivel

    def conectar():
        raise psycopg.OperationalError('connection to server at "localhost", port 5432 failed')

    consultor = ConsultorSQL(conectar=conectar, timeout_ms=5000, limite_linhas=200)

    with pytest.raises(BancoIndisponivel) as erro:
        consultor.consultar("SELECT uf FROM despesas")
    assert "localhost" not in str(erro.value) and "5432" not in str(erro.value)


def test_conexao_perdida_durante_a_consulta_vira_banco_indisponivel():
    from src.tools.consultar_sql import BancoIndisponivel

    conexao = ConexaoFalsa(erro=psycopg.OperationalError("server closed the connection"))

    with pytest.raises(BancoIndisponivel):
        _consultor(conexao).consultar("SELECT uf FROM despesas")
