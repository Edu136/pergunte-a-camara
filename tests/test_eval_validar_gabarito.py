"""STORY-006, RN10: validação do gabarito no banco. Cenários H5, E3, E4, X4, X5."""

import pytest

from src.eval.conjunto import ItemAvaliacao
from src.eval.validar_gabarito import BANCO_INDISPONIVEL, main, validar_gabarito
from src.tools.consultar_sql import BancoIndisponivel, ErroExecucaoSQL, ResultadoConsulta
from src.tools.sql_guard import SQLInvalido

CATEGORIAS = ["PASSAGEM AÉREA - SIGEPA", "TELEFONIA"]


def _respondivel(id_, sql="SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024"):
    categoria = {"F": "facil", "M": "media", "D": "dificil"}[id_[0]]
    return ItemAvaliacao(id=id_, categoria=categoria, pergunta=f"Pergunta {id_} de teste?",
                         respondida=True, sql=sql)


def _opiniao(id_="O01"):
    return ItemAvaliacao(id=id_, categoria="opiniao", pergunta="Quem desperdiça mais a cota?",
                         respondida=False)


class ConsultorFalso:
    """Devolve, por SQL, linhas ou lança a exceção configurada."""

    def __init__(self, respostas=None, padrao=({"total": 10.5},)):
        self.respostas = respostas or {}
        self.padrao = list(padrao)
        self.executados = []

    def consultar(self, sql):
        self.executados.append(sql)
        resposta = self.respostas.get(sql, self.padrao)
        if isinstance(resposta, Exception):
            raise resposta
        return ResultadoConsulta(sql=sql, linhas=list(resposta))


def _rodar(itens, consultor, categorias=lambda: CATEGORIAS):
    saida = []
    codigo = validar_gabarito(itens, consultor, categorias, escrever=saida.append)
    return codigo, saida


def test_h5_gabarito_sem_falhas():
    consultor = ConsultorFalso()
    sql_m = "SELECT uf, SUM(valor_liquido) FROM despesas GROUP BY uf"
    codigo, saida = _rodar([_respondivel("M01", sql_m), _opiniao(), _respondivel("F01")],
                           consultor)

    assert codigo == 0
    assert saida[0].startswith("OK    F01 (") and saida[0].endswith(" ms)")
    assert saida[1].startswith("OK    M01 (")
    assert saida[-1] == "Gabarito: 2 ok, 0 falhas de 2."
    assert len(consultor.executados) == 2


def test_e3_so_nulos_e_sem_dados():
    codigo, saida = _rodar([_respondivel("F01")], ConsultorFalso(padrao=[{"total": None}]))
    assert codigo == 1
    assert "FALHA F01: sem dados" in saida


def test_e4_sem_linhas_e_sem_dados():
    codigo, saida = _rodar([_respondivel("F01")], ConsultorFalso(padrao=[]))
    assert codigo == 1
    assert "FALHA F01: sem dados" in saida


def test_x4_falhas_listadas_com_motivo():
    sql_categoria = "SELECT SUM(valor_liquido) FROM despesas WHERE categoria = 'TELEFONE'"
    sql_lento = "SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2025"
    timeout = ErroExecucaoSQL("A consulta excedeu o tempo limite de 5000 ms: filtre ou agregue.")
    consultor = ConsultorFalso(respostas={sql_lento: timeout})

    itens = [_respondivel("F01", sql_categoria), _respondivel("F02", sql_lento),
             _respondivel("F03")]
    codigo, saida = _rodar(itens, consultor)

    assert codigo == 1
    assert saida[0].startswith("FALHA F01: Categoria 'TELEFONE' não existe")
    assert "TELEFONIA" in saida[0]
    assert saida[1].startswith("FALHA F02: A consulta excedeu o tempo limite")
    assert saida[2].startswith("OK    F03 (")
    assert saida[-1] == "Gabarito: 1 ok, 2 falhas de 3."
    assert sql_categoria not in consultor.executados


def test_x4_sql_barrado_pelo_guard_na_execucao_e_falha():
    # O schema já barra o gabarito inseguro na carga; aqui o guard da execução recusa mesmo assim
    # (ex.: limite de linhas configurado diferente), e o validador reporta como falha.
    sql = "SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024"
    consultor = ConsultorFalso(respostas={sql: SQLInvalido("Tabelas não permitidas: pg_user")})
    codigo, saida = _rodar([_respondivel("F01", sql)], consultor)
    assert codigo == 1
    assert saida[0] == "FALHA F01: Tabelas não permitidas: pg_user"


def test_x5_banco_indisponivel_aborta_antes_dos_itens():
    def categorias():
        raise BancoIndisponivel("O banco de dados está indisponível no momento.")

    consultor = ConsultorFalso()
    codigo, saida = _rodar([_respondivel("F01")], consultor, categorias)

    assert codigo == 2
    assert saida == [BANCO_INDISPONIVEL]
    assert BANCO_INDISPONIVEL == (
        "Banco indisponível: suba o Postgres e carregue os dados antes de validar o gabarito."
    )
    assert consultor.executados == []


def test_x5_banco_cai_no_meio_tambem_aborta():
    consultor = ConsultorFalso(padrao=[])
    consultor.respostas = {
        "SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024":
            BancoIndisponivel("O banco de dados está indisponível no momento.")
    }
    codigo, saida = _rodar([_respondivel("F01"), _respondivel("F02")], consultor)
    assert codigo == 2
    assert saida == [BANCO_INDISPONIVEL]


def test_erro_ao_listar_categorias_aborta_com_mensagem():
    def categorias():
        raise ErroExecucaoSQL('Erro no banco: relation "despesas" does not exist')

    consultor = ConsultorFalso()
    codigo, saida = _rodar([_respondivel("F01")], consultor, categorias)

    assert codigo == 2
    assert saida == [
        'Não foi possível listar as categorias: Erro no banco: relation "despesas" does not exist'
    ]
    assert consultor.executados == []


def test_main_com_conjunto_invalido_sai_com_mensagem(tmp_path, monkeypatch, capsys):
    caminho = tmp_path / "conjunto.json"
    caminho.write_text("[{", encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["validar_gabarito", "--conjunto", str(caminho)])

    with pytest.raises(SystemExit) as saida:
        main()

    assert saida.value.code == 1
    assert "Conjunto de avaliação com JSON inválido" in capsys.readouterr().out
