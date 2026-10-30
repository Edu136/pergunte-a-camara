"""Loop do agente: o LLM escreve SQL, a ferramenta valida e executa, o resultado volta ao LLM
delimitado, até a resposta final. Regras em specs/STORY-001/spec.bdd.md e fluxo no blueprint.
"""

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any, Protocol

from src.agent.prompts import FERRAMENTAS, formatar_dados, montar_prompt_sistema
from src.config import Settings, settings
from src.llm.cliente import ChamadaFerramenta, ClienteLLM, LLMIndisponivel
from src.schemas import Grafico, PassoAgente, Resposta
from src.tools.consultar_sql import BancoIndisponivel, ErroExecucaoSQL, ResultadoConsulta
from src.tools.grafico import escolher_grafico
from src.tools.sql_guard import SQLInvalido
from src.tools.validar_categorias import validar_categorias

log = logging.getLogger(__name__)

FONTE_CEAP = (
    "Câmara dos Deputados — Dados abertos da Cota para o Exercício da Atividade Parlamentar "
    "(CEAP): https://www.camara.leg.br/cotas"
)
SQL_CATEGORIAS = "SELECT DISTINCT categoria FROM despesas ORDER BY categoria"

SEM_DADOS = "Não foi possível responder com os dados disponíveis."
LLM_FORA = "O modelo de linguagem está indisponível no momento. Tente novamente mais tarde."
BANCO_FORA = "O banco de dados está indisponível no momento. Tente novamente mais tarde."
LIMITE_PASSOS = "A pergunta exigiu mais consultas que o limite de passos do agente."
CORRECOES_ESGOTADAS = "Não consegui montar uma consulta válida para essa pergunta."


def _linhas(total: int) -> str:
    return f"{total} linha{'s' if total != 1 else ''}"


class Consultor(Protocol):
    def consultar(self, sql: str) -> ResultadoConsulta: ...


class Registro(Protocol):
    def registrar(self, id_pergunta: str, pergunta: str, passo: PassoAgente) -> None: ...


class Agente:
    def __init__(
        self,
        llm: ClienteLLM,
        consultor: Consultor,
        config: Settings = settings,
        registro: Registro | None = None,
    ):
        self.llm = llm
        self.consultor = consultor
        self.config = config
        self.registro = registro
        self._categorias: list[str] | None = None

    def responder(
        self, pergunta: str, ao_passo: Callable[[PassoAgente], None] | None = None
    ) -> Resposta:
        """Responde a pergunta. ao_passo é avisado de cada passo assim que ele é registrado."""
        id_pergunta = uuid.uuid4().hex
        mensagens: list[dict[str, Any]] = [
            {"role": "system", "content": montar_prompt_sistema(self._listar_categorias())},
            {"role": "user", "content": pergunta},
        ]
        passos: list[PassoAgente] = []
        ultimo_sucesso: ResultadoConsulta | None = None
        falhas_seguidas = 0

        def anotar(passo: PassoAgente) -> None:
            passos.append(passo)
            if self.registro:
                self.registro.registrar(id_pergunta, pergunta, passo)
            if ao_passo:
                ao_passo(passo)

        def nao_respondida(explicacao: str) -> Resposta:
            return Resposta(
                pergunta=pergunta, explicacao=explicacao, passos=passos, respondida=False
            )

        while True:
            try:
                mensagem = self.llm.conversar(mensagens, FERRAMENTAS)
            except LLMIndisponivel as erro:
                log.warning("LLM indisponível: %s", erro)
                return nao_respondida(LLM_FORA)

            if not mensagem.chamadas:
                if ultimo_sucesso is None:
                    return nao_respondida(SEM_DADOS)
                grafico, passo = self._escolher_grafico(ultimo_sucesso.linhas)
                anotar(passo)
                return Resposta(
                    pergunta=pergunta,
                    sql=ultimo_sucesso.sql,
                    dados=ultimo_sucesso.linhas,
                    grafico=grafico,
                    explicacao=mensagem.conteudo,
                    fontes=[FONTE_CEAP],
                    passos=passos,
                )

            mensagens.append({
                "role": "assistant",
                "content": mensagem.conteudo,
                "tool_calls": [
                    {"function": {"name": c.nome, "arguments": c.argumentos}}
                    for c in mensagem.chamadas
                ],
            })
            for chamada in mensagem.chamadas:
                if len(passos) >= self.config.agente_max_passos:
                    return nao_respondida(LIMITE_PASSOS)

                passo, resultado, conteudo = self._executar(chamada)
                anotar(passo)
                if conteudo is None:
                    return nao_respondida(BANCO_FORA)
                mensagens.append({"role": "tool", "tool_name": chamada.nome, "content": conteudo})

                if resultado is not None:
                    ultimo_sucesso, falhas_seguidas = resultado, 0
                    continue
                falhas_seguidas += 1
                if falhas_seguidas > self.config.agente_max_correcoes:
                    return nao_respondida(CORRECOES_ESGOTADAS)

    def _escolher_grafico(self, linhas: list[dict[str, Any]]) -> tuple[Grafico | None, PassoAgente]:
        """Escolha por regras fixas (ADR-002), registrada como passo para a demo e o log."""
        inicio = time.perf_counter()
        grafico = escolher_grafico(linhas, self.config.grafico_max_barras)
        passo = PassoAgente(
            ferramenta="gerar_grafico",
            descricao="Escolha automática do gráfico",
            saida=grafico.tipo if grafico else "sem gráfico",
            duracao_ms=round((time.perf_counter() - inicio) * 1000),
        )
        return grafico, passo

    def _listar_categorias(self) -> list[str]:
        """Categorias reais para o prompt, buscadas uma vez. Sem banco, segue sem elas."""
        if self._categorias is None:
            try:
                linhas = self.consultor.consultar(SQL_CATEGORIAS).linhas
            except (SQLInvalido, ErroExecucaoSQL, BancoIndisponivel) as erro:
                log.warning("Não foi possível listar as categorias: %s", erro)
                return []
            self._categorias = [linha["categoria"] for linha in linhas]
        return self._categorias

    def _executar(
        self, chamada: ChamadaFerramenta
    ) -> tuple[PassoAgente, ResultadoConsulta | None, str | None]:
        """Executa uma chamada de ferramenta: devolve o passo, o resultado e o texto para o LLM.

        Texto None indica falha de infraestrutura (banco fora): não há o que o modelo corrigir.
        """
        inicio = time.perf_counter()
        resultado = None
        banco_fora = False
        sql = chamada.argumentos.get("sql")

        if chamada.nome != "consultar_sql":
            erro = f"Ferramenta desconhecida: {chamada.nome}. Use consultar_sql."
        elif not isinstance(sql, str) or not sql.strip():
            erro = "Argumento obrigatório 'sql' ausente ou vazio."
        else:
            try:
                validar_categorias(sql, self._categorias or [])
                resultado = self.consultor.consultar(sql)
                erro = None
            except (SQLInvalido, ErroExecucaoSQL) as falha:
                erro = str(falha)
            except BancoIndisponivel as falha:
                erro, banco_fora = str(falha), True

        passo = PassoAgente(
            ferramenta=chamada.nome,
            descricao="Consulta ao banco de dados",
            entrada=chamada.argumentos,
            saida=_linhas(len(resultado.linhas)) if resultado else None,
            erro=erro,
            duracao_ms=round((time.perf_counter() - inicio) * 1000),
            sucesso=resultado is not None,
        )
        if banco_fora:
            return passo, None, None
        if resultado is None:
            return passo, None, f"Erro: {erro} Corrija e tente novamente."
        return passo, resultado, formatar_dados(
            resultado.linhas, self.config.agente_linhas_para_llm
        )
