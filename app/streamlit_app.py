"""Demo em Streamlit: cliente da API POST /perguntar que mostra os passos do agente em tempo real.

A página só desenha; a leitura do stream fica em src/api/cliente.py.
Regras em specs/STORY-005/spec.bdd.md e fluxo no blueprint.
"""

import re
import sys
from pathlib import Path

# `streamlit run` põe só app/ no sys.path; a raiz do repositório é necessária para `import src`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from pydantic import ValidationError

from src.api import cliente
from src.schemas import Grafico, PassoAgente, Pergunta, Resposta
from src.tools.grafico import TITULO_TABELA, montar_figura

PERGUNTAS_EXEMPLO = [
    "Quanto foi gasto por UF em 2025?",
    "Como variaram os gastos com passagens aéreas por mês em 2024?",
    "Quais categorias tiveram os maiores valores em 2025?",
    "Quanto foi gasto no total em 2024?",
]
PERGUNTA_INVALIDA = "A pergunta precisa ter entre 5 e 500 caracteres."
AVISO_FONTE = "Verifique na fonte oficial antes de usar estes números."
EM_ANDAMENTO = "Consultando os dados…"
CONCLUIDO = "Concluído"
NAO_CONCLUIDO = "Não foi possível concluir"
PONTUACAO_ASCII = re.compile(r"([!-/:-@\[-`{-~])")


def escapar(texto: str) -> str:
    """Escapa toda a pontuação ASCII para o markdown exibir o texto como veio: sem links, imagens,
    fórmulas ("R$ 10 e R$ 20") nem formatação vindos do LLM ou do banco."""
    return PONTUACAO_ASCII.sub(r"\\\1", texto)


def linha_do_passo(passo: PassoAgente) -> str:
    icone = "✅" if passo.sucesso else "❌"
    resultado = passo.saida if passo.sucesso else passo.erro
    duracao = f"{passo.duracao_ms / 1000:.1f}".replace(".", ",")
    return f"{icone} {passo.descricao}: {resultado} ({duracao} s)"


def desenhar_passo(passo: PassoAgente) -> None:
    st.text(linha_do_passo(passo))
    if sql := passo.entrada.get("sql"):
        st.code(sql, language="sql")


def situacao(final: cliente.Evento) -> dict[str, str]:
    if isinstance(final, cliente.RespostaRecebida):
        return {"label": CONCLUIDO, "state": "complete"}
    return {"label": NAO_CONCLUIDO, "state": "error"}


def desenhar_resposta(resposta: Resposta) -> None:
    if not resposta.respondida:
        st.warning(escapar(resposta.explicacao))
        return
    st.text(resposta.explicacao)  # texto do LLM: sem markdown, links nem imagens
    grafico = resposta.grafico
    if grafico and grafico.tipo in ("linha", "barra"):
        st.plotly_chart(montar_figura(grafico, resposta.dados))
    if resposta.dados:
        colunas = list(resposta.dados[0])
        tabela = Grafico(tipo="tabela", eixo_x=colunas[0], eixo_y=colunas[0], titulo=TITULO_TABELA)
        st.plotly_chart(montar_figura(tabela, resposta.dados))
    if resposta.sql:
        st.code(resposta.sql, language="sql")
    for fonte in resposta.fontes:
        st.markdown(f"Fonte: {fonte}")  # constante do agente; em markdown para virar link
    st.info(AVISO_FONTE)


def desenhar_final(final: cliente.Evento) -> None:
    if isinstance(final, cliente.RespostaRecebida):
        desenhar_resposta(final.resposta)
    elif isinstance(final, cliente.Falha):
        st.error(final.mensagem)


def executar(texto: str) -> None:
    """Desenha os passos assim que chegam e guarda a execução para as próximas reexecuções."""
    passos: list[PassoAgente] = []
    final = None
    with st.status(EM_ANDAMENTO, expanded=True) as status:
        for evento in cliente.perguntar(texto):
            if isinstance(evento, cliente.PassoRecebido):
                passos.append(evento.passo)
                desenhar_passo(evento.passo)
            else:
                final = evento
        status.update(**situacao(final), expanded=False)
    st.session_state["ultima"] = {"passos": passos, "final": final}
    desenhar_final(final)


def redesenhar(ultima: dict) -> None:
    """Reexecução sem envio: mostra a última execução salva, sem chamar a API."""
    with st.status(**situacao(ultima["final"]), expanded=False):
        for passo in ultima["passos"]:
            desenhar_passo(passo)
    desenhar_final(ultima["final"])


def enviar_exemplo() -> None:
    """Clique numa pergunta de exemplo: preenche o campo e envia."""
    pergunta = st.session_state["exemplo"]
    if pergunta:
        st.session_state["texto"] = pergunta
        st.session_state["enviar"] = pergunta
        st.session_state["exemplo"] = None


st.title("Pergunte à Câmara")
st.caption("Perguntas sobre os gastos da cota parlamentar, com dados abertos oficiais.")

st.pills("Experimente", PERGUNTAS_EXEMPLO, key="exemplo", on_change=enviar_exemplo)
with st.form("pergunta"):
    texto = st.text_input("Sua pergunta", key="texto", max_chars=500)
    if st.form_submit_button("Perguntar"):
        st.session_state["enviar"] = texto

enviada = st.session_state.pop("enviar", None)
if enviada is not None:
    try:
        Pergunta(texto=enviada)
    except ValidationError:
        st.warning(PERGUNTA_INVALIDA)
    else:
        executar(enviada)
elif "ultima" in st.session_state:
    redesenhar(st.session_state["ultima"])
