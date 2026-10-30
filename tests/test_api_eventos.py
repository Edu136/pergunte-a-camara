"""Gerador de eventos SSE da API (STORY-004): ordem, tempo real, thread e erro sem vazamento."""

import inspect
import json
import logging
import threading

from src.api.main import ERRO_INESPERADO, eventos
from src.schemas import PassoAgente, Resposta

PASSO = PassoAgente(ferramenta="consultar_sql", descricao="Consulta ao banco de dados")


def ler(linhas):
    """Converte o texto SSE em [(evento, data decodificado)]."""
    resultado = []
    for bloco in "".join(linhas).split("\n\n"):
        if not bloco:
            continue
        evento, dados = bloco.split("\n")
        assert evento.startswith("event: ") and dados.startswith("data: ")
        resultado.append((evento[len("event: "):], json.loads(dados[len("data: "):])))
    return resultado


class AgenteRoteirizado:
    """Avisa os passos dados e então devolve a resposta ou lança a exceção."""

    def __init__(self, passos=(), fim=None, liberar=None):
        self.passos = list(passos)
        self.fim = fim
        self.liberar = liberar
        self.thread = None
        self.terminou = False

    def responder(self, pergunta, ao_passo=None):
        self.thread = threading.current_thread()
        for passo in self.passos:
            ao_passo(passo)
        if self.liberar:
            assert self.liberar.wait(timeout=5)
        self.terminou = True
        if isinstance(self.fim, Exception):
            raise self.fim
        return self.fim or Resposta(pergunta=pergunta, explicacao="Pronto.", passos=self.passos)


def test_h2_passo_chega_antes_de_o_agente_terminar():
    liberar = threading.Event()
    agente = AgenteRoteirizado([PASSO], liberar=liberar)
    gerador = eventos(agente, "Quanto por UF?")

    primeiro = ler([next(gerador)])

    assert primeiro == [("passo", PASSO.model_dump(mode="json"))]
    assert not agente.terminou
    liberar.set()
    resto = ler(list(gerador))
    assert [evento for evento, _ in resto] == ["resposta"]
    assert resto[0][1]["passos"] == [PASSO.model_dump(mode="json")]


def test_e2_acentos_intactos_e_data_numa_linha():
    explicacao = "Despesas com divulgação\nsomaram R$ 10,00."
    agente = AgenteRoteirizado(fim=Resposta(pergunta="p", explicacao=explicacao))

    texto = "".join(eventos(agente, "Quanto em divulgação?"))

    assert "divulgação" in texto and "\\u" not in texto
    assert texto.count("\n") == 3  # event, data e a linha em branco final
    assert ler([texto])[0][1]["explicacao"] == explicacao


def test_e5_agente_roda_fora_da_thread_que_consome():
    agente = AgenteRoteirizado([PASSO])

    list(eventos(agente, "Quanto por UF?"))

    assert inspect.isgeneratorfunction(eventos)
    assert agente.thread is not None and agente.thread is not threading.current_thread()


def test_x2_excecao_depois_de_um_passo_vira_erro_generico(caplog):
    agente = AgenteRoteirizado([PASSO], fim=RuntimeError("detalhe interno SELECT secreto"))

    with caplog.at_level(logging.ERROR):
        texto = "".join(eventos(agente, "Quanto por UF?"))

    assert [evento for evento, _ in ler([texto])] == ["passo", "erro"]
    assert ler([texto])[1][1] == {"mensagem": ERRO_INESPERADO}
    for proibido in ("detalhe interno", "SELECT secreto", "Traceback"):
        assert proibido not in texto
    assert "detalhe interno SELECT secreto" in caplog.text


def test_x3_excecao_antes_de_qualquer_passo():
    agente = AgenteRoteirizado(fim=ValueError("falhou cedo"))

    assert ler(list(eventos(agente, "Quanto por UF?"))) == [
        ("erro", {"mensagem": ERRO_INESPERADO})]
