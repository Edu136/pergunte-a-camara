import pytest

from src.tools.sql_guard import SQLInvalido, validar_sql


def test_select_simples_ganha_limit():
    sql = validar_sql("SELECT categoria, SUM(valor_liquido) FROM despesas GROUP BY categoria")
    assert "LIMIT 200" in sql


def test_limit_acima_do_maximo_e_reduzido():
    sql = validar_sql("SELECT * FROM despesas LIMIT 10000", limite_maximo=50)
    assert "LIMIT 50" in sql


def test_limit_dentro_do_maximo_e_mantido():
    sql = validar_sql("SELECT * FROM despesas LIMIT 10")
    assert "LIMIT 10" in sql


def test_join_entre_tabelas_permitidas():
    validar_sql(
        "SELECT d.nome, SUM(x.valor_liquido) FROM despesas x "
        "JOIN deputados d ON d.id = x.deputado_id GROUP BY d.nome"
    )


def test_cte_e_permitida():
    validar_sql("WITH t AS (SELECT * FROM despesas) SELECT COUNT(*) FROM t")


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM despesas",
        "DROP TABLE deputados",
        "UPDATE despesas SET valor_liquido = 0",
        "SELECT 1; DROP TABLE despesas",
        "SELECT * FROM pg_user",
        "SELECT * FROM documentos",
    ],
)
def test_comandos_perigosos_sao_bloqueados(sql):
    with pytest.raises(SQLInvalido):
        validar_sql(sql)
