import copy

from src.agent.agente import FONTE_CEAP, SQL_CATEGORIAS, Agente
from src.config import Settings
from src.llm.cliente import ChamadaFerramenta, LLMIndisponivel, MensagemLLM
from src.tools.consultar_sql import ErroExecucaoSQL, ResultadoConsulta
from src.tools.sql_guard import validar_sql

SQL_UF = "SELECT uf, SUM(valor_liquido) AS total FROM despesas GROUP BY uf"
SQL_CAT = "SELECT categoria, SUM(valor_liquido) AS total FROM despesas GROUP BY categoria"
LINHAS_UF = [{"uf": "MG", "total": 10.0}, {"uf": "SP", "total": 5.0}]


class LLMRoteirizado:
    """Devolve as mensagens do roteiro em ordem e guarda a conversa recebida a cada chamada."""

    def __init__(self, *roteiro):
        self.roteiro = list(roteiro)
        self.conversas = []

    def conversar(self, mensagens, ferramentas):
        self.conversas.append(copy.deepcopy(mensagens))
        item = self.roteiro.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class ConsultorFalso:
    """Passa pelo sql_guard real e devolve os resultados roteirizados em ordem."""

    def __init__(self, *resultados, categorias=("PASSAGEM AÉREA - SIGEPA",)):
        self.resultados = list(resultados)
        self.categorias = list(categorias)
        self.executados = []
        self.consultas_categorias = 0

    def consultar(self, sql):
        if sql == SQL_CATEGORIAS:
            self.consultas_categorias += 1
            return ResultadoConsulta(sql, [{"categoria": c} for c in self.categorias])
        sql_validado = validar_sql(sql)
        item = self.resultados.pop(0)
        if isinstance(item, Exception):
            raise item
        self.executados.append(sql_validado)
        return ResultadoConsulta(sql_validado, item)


def sql(consulta):
    return MensagemLLM("", [ChamadaFerramenta("consultar_sql", {"sql": consulta})])


def texto(conteudo):
    return MensagemLLM(conteudo)


def config(**valores):
    return Settings(_env_file=None, **valores)


def _agente(llm, consultor, **valores):
    return Agente(llm=llm, consultor=consultor, config=config(**valores))


def _resultados_de_ferramenta(conversa):
    return [m["content"] for m in conversa if m["role"] == "tool"]


def _consultas(resposta):
    """Passos de consultar_sql (o passo automático gerar_grafico fica de fora)."""
    return [p for p in resposta.passos if p.ferramenta == "consultar_sql"]


# --- Happy path ---------------------------------------------------------------------------

def test_h1_pergunta_respondida_com_uma_consulta():
    llm = LLMRoteirizado(sql(SQL_UF), texto("MG gastou mais."))
    consultor = ConsultorFalso(LINHAS_UF)

    resposta = _agente(llm, consultor).responder("Quanto cada UF gastou?")

    assert resposta.respondida is True
    assert resposta.sql == consultor.executados[0] and "LIMIT 200" in resposta.sql
    assert resposta.dados == LINHAS_UF
    assert resposta.explicacao == "MG gastou mais."
    assert resposta.fontes == [FONTE_CEAP]
    assert len(_consultas(resposta)) == 1
    passo = _consultas(resposta)[0]
    assert passo.ferramenta == "consultar_sql" and passo.sucesso is True
    assert passo.entrada == {"sql": SQL_UF} and passo.saida == "2 linhas"


def test_h2_resultado_vazio_e_resposta_valida():
    llm = LLMRoteirizado(sql(SQL_UF), texto("Não há registros."))

    resposta = _agente(llm, ConsultorFalso([])).responder("Gastos em 1990?")

    assert resposta.respondida is True and resposta.dados == []


def test_h3_autocorrecao_apos_sql_rejeitado_pelo_guard():
    llm = LLMRoteirizado(sql("DELETE FROM despesas"), sql(SQL_UF), texto("Pronto."))

    resposta = _agente(llm, ConsultorFalso(LINHAS_UF)).responder("Apague tudo e some por UF")

    erro_recebido = _resultados_de_ferramenta(llm.conversas[1])[0]
    assert "Apenas consultas SELECT" in erro_recebido
    assert resposta.respondida is True and "SUM" in resposta.sql
    assert resposta.passos[0].sucesso is False and resposta.passos[0].erro


def test_h4_autocorrecao_apos_erro_no_banco():
    erro = ErroExecucaoSQL('Erro no banco: column "valor" does not exist')
    llm = LLMRoteirizado(sql("SELECT valor FROM despesas"), sql(SQL_UF), texto("Pronto."))

    resposta = _agente(llm, ConsultorFalso(erro, LINHAS_UF)).responder("Quanto por UF?")

    assert 'column "valor" does not exist' in _resultados_de_ferramenta(llm.conversas[1])[0]
    assert resposta.respondida is True


def test_h5_vale_a_ultima_consulta_bem_sucedida():
    linhas_cat = [{"categoria": "X", "total": 1.0}]
    llm = LLMRoteirizado(sql(SQL_UF), sql(SQL_CAT), texto("Pronto."))
    consultor = ConsultorFalso(LINHAS_UF, linhas_cat)

    resposta = _agente(llm, consultor).responder("Compare UF e categoria")

    assert resposta.sql == consultor.executados[1] and resposta.dados == linhas_cat
    assert [p.entrada["sql"] for p in _consultas(resposta)] == [SQL_UF, SQL_CAT]


def test_h7_categorias_reais_no_prompt_buscadas_uma_vez():
    consultor = ConsultorFalso(LINHAS_UF, LINHAS_UF, categorias=["COMBUSTÍVEIS E LUBRIFICANTES."])
    agente = _agente(LLMRoteirizado(sql(SQL_UF), texto("a"), sql(SQL_UF), texto("b")), consultor)

    agente.responder("Pergunta um")
    agente.responder("Pergunta dois")

    sistema = agente.llm.conversas[0][0]
    assert sistema["role"] == "system" and "COMBUSTÍVEIS E LUBRIFICANTES." in sistema["content"]
    assert consultor.consultas_categorias == 1


# --- Edge cases ---------------------------------------------------------------------------

def test_e1_modelo_recebe_dados_delimitados_e_truncados_resposta_tem_tudo():
    linhas = [{"uf": f"U{i}", "total": float(i)} for i in range(5)]
    llm = LLMRoteirizado(sql(SQL_UF), texto("Pronto."))

    resposta = _agente(llm, ConsultorFalso(linhas), agente_linhas_para_llm=3).responder("Por UF")

    conteudo = _resultados_de_ferramenta(llm.conversas[1])[0]
    assert "<dados>" in conteudo and "3 de 5" in conteudo
    assert resposta.dados == linhas


def test_e2_teto_de_passos():
    llm = LLMRoteirizado(sql(SQL_UF), sql(SQL_UF), sql(SQL_UF), texto("nunca chega"))
    consultor = ConsultorFalso(LINHAS_UF, LINHAS_UF, LINHAS_UF)

    resposta = _agente(llm, consultor, agente_max_passos=2).responder("Repita")

    assert len(consultor.executados) == 2
    assert resposta.respondida is False and "limite de passos" in resposta.explicacao


def test_e3_varias_chamadas_numa_mensagem():
    duas = MensagemLLM("", [ChamadaFerramenta("consultar_sql", {"sql": SQL_UF}),
                            ChamadaFerramenta("consultar_sql", {"sql": SQL_CAT})])
    llm = LLMRoteirizado(duas, texto("Pronto."))

    resposta = _agente(llm, ConsultorFalso(LINHAS_UF, [])).responder("Duas coisas")

    assert len(_consultas(resposta)) == 2
    assert len(_resultados_de_ferramenta(llm.conversas[1])) == 2


def test_e4_modelo_responde_sem_consultar():
    llm = LLMRoteirizado(texto("Foram R$ 1 milhão."))

    resposta = _agente(llm, ConsultorFalso()).responder("Quanto gastaram?")

    assert resposta.respondida is False and resposta.sql is None and resposta.dados == []
    assert "R$ 1 milhão" not in resposta.explicacao
    assert "dados disponíveis" in resposta.explicacao


def test_e6_sucesso_zera_o_contador_de_falhas():
    llm = LLMRoteirizado(sql("DROP TABLE x"), sql(SQL_UF), sql("DROP TABLE x"), sql(SQL_UF),
                         texto("Pronto."))

    resposta = _agente(llm, ConsultorFalso(LINHAS_UF, LINHAS_UF),
                       agente_max_correcoes=1).responder("Insista")

    assert resposta.respondida is True


# --- Error cases --------------------------------------------------------------------------

def test_x1_correcoes_esgotadas():
    llm = LLMRoteirizado(*[sql("DROP TABLE despesas")] * 4)

    resposta = _agente(llm, ConsultorFalso(), agente_max_correcoes=2).responder("Apague")

    assert len(llm.conversas) == 3
    assert resposta.respondida is False and resposta.sql is None
    assert "consulta válida" in resposta.explicacao
    assert len(resposta.passos) == 3


def test_x2_ferramenta_desconhecida():
    chamada = MensagemLLM("", [ChamadaFerramenta("apagar_tudo", {})])
    llm = LLMRoteirizado(chamada, sql(SQL_UF), texto("Pronto."))
    consultor = ConsultorFalso(LINHAS_UF)

    resposta = _agente(llm, consultor).responder("Teste")

    assert "ferramenta desconhecida" in _resultados_de_ferramenta(llm.conversas[1])[0].lower()
    assert resposta.passos[0].ferramenta == "apagar_tudo" and resposta.passos[0].sucesso is False
    assert len(consultor.executados) == 1


def test_x3_argumentos_invalidos():
    chamada = MensagemLLM("", [ChamadaFerramenta("consultar_sql", {})])
    llm = LLMRoteirizado(chamada, sql(SQL_UF), texto("Pronto."))
    consultor = ConsultorFalso(LINHAS_UF)

    _agente(llm, consultor).responder("Teste")

    assert "sql" in _resultados_de_ferramenta(llm.conversas[1])[0]
    assert len(consultor.executados) == 1


def test_x4_llm_indisponivel():
    llm = LLMRoteirizado(LLMIndisponivel("Ollama indisponível"))

    resposta = _agente(llm, ConsultorFalso()).responder("Quanto?")

    assert resposta.respondida is False
    assert "modelo de linguagem está indisponível" in resposta.explicacao


def test_e7_sem_categorias_o_agente_segue_e_tenta_de_novo_depois():
    class ConsultorSemCategorias(ConsultorFalso):
        def consultar(self, sql):
            if sql == SQL_CATEGORIAS and self.consultas_categorias == 0:
                self.consultas_categorias += 1
                raise ErroExecucaoSQL("Erro no banco: conexão recusada")
            return super().consultar(sql)

    consultor = ConsultorSemCategorias([{"uf": "MG", "total": 1.0}], LINHAS_UF)
    llm = LLMRoteirizado(sql(SQL_UF), texto("a"), sql(SQL_UF), texto("b"))
    agente = _agente(llm, consultor)

    primeira = agente.responder("Pergunta um")
    agente.responder("Pergunta dois")

    assert primeira.respondida is True and primeira.passos[0].saida == "1 linha"
    assert consultor.consultas_categorias == 2


def test_x12_banco_indisponivel_encerra_sem_gastar_correcoes():
    from src.tools.consultar_sql import BancoIndisponivel

    llm = LLMRoteirizado(sql(SQL_UF), sql(SQL_UF), sql(SQL_UF))
    falha = BancoIndisponivel("O banco de dados está indisponível no momento.")

    resposta = _agente(llm, ConsultorFalso(falha)).responder("Quanto por UF?")

    assert len(llm.conversas) == 1
    assert resposta.respondida is False
    assert "banco de dados está indisponível" in resposta.explicacao
    assert resposta.passos[0].sucesso is False


# --- STORY-002: validação de categorias ----------------------------------------------------

SQL_COMB = "SELECT SUM(valor_liquido) AS total FROM despesas WHERE categoria = '{}'"
COMBUSTIVEIS = "COMBUSTÍVEIS E LUBRIFICANTES."


def test_story002_h2_agente_corrige_categoria_pela_sugestao():
    llm = LLMRoteirizado(sql(SQL_COMB.format("COMBUSTÍVEIS E LUBRIFICANTES")),
                         sql(SQL_COMB.format(COMBUSTIVEIS)), texto("Pronto."))
    consultor = ConsultorFalso([{"total": 10.0}], categorias=[COMBUSTIVEIS])

    resposta = _agente(llm, consultor).responder("Gasto com combustíveis?")

    assert len(consultor.executados) == 1
    assert f"'{COMBUSTIVEIS}'" in _resultados_de_ferramenta(llm.conversas[1])[0]
    assert resposta.respondida is True and COMBUSTIVEIS in resposta.sql


def test_story002_x2_categoria_errada_conta_para_o_limite():
    llm = LLMRoteirizado(*[sql(SQL_COMB.format("COMBUSTÍVEL"))] * 3)
    consultor = ConsultorFalso(categorias=[COMBUSTIVEIS])

    resposta = _agente(llm, consultor, agente_max_correcoes=1).responder("Combustível?")

    assert consultor.executados == []
    assert resposta.respondida is False


# --- STORY-003: gráfico ----------------------------------------------------------------------

def test_story003_h3_agente_preenche_grafico_e_registra_o_passo():
    llm = LLMRoteirizado(sql(SQL_UF), texto("MG gastou mais."))

    resposta = _agente(llm, ConsultorFalso(LINHAS_UF)).responder("Quanto cada UF gastou?")

    assert resposta.grafico.tipo == "barra" and resposta.grafico.eixo_x == "uf"
    passo = resposta.passos[-1]
    assert passo.ferramenta == "gerar_grafico" and passo.sucesso is True
    assert passo.descricao == "Escolha automática do gráfico" and passo.saida == "barra"


def test_story003_valor_unico_registra_sem_grafico():
    llm = LLMRoteirizado(sql("SELECT SUM(valor_liquido) AS total FROM despesas"), texto("ok"))

    resposta = _agente(llm, ConsultorFalso([{"total": 1.0}])).responder("Total?")

    assert resposta.grafico is None and resposta.passos[-1].saida == "sem gráfico"


def test_story003_x2_nao_respondida_sem_grafico_nem_passo():
    resposta = _agente(LLMRoteirizado(texto("Foram R$ 1 milhão.")), ConsultorFalso()).responder("?")

    assert resposta.grafico is None
    assert all(p.ferramenta != "gerar_grafico" for p in resposta.passos)
