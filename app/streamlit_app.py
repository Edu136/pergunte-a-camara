"""Demo em Streamlit: cliente da API POST /perguntar que mostra os passos do agente em tempo real.

A página só desenha; a leitura do stream fica em src/api/cliente.py.
Regras em specs/STORY-005/spec.bdd.md e fluxo no blueprint.
"""

import sys
from pathlib import Path

# `streamlit run` põe só app/ no sys.path; a raiz do repositório é necessária para `import src`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from src.api import cliente  # noqa: E402
from src.schemas import PassoAgente, Pergunta  # noqa: E402

PERGUNTAS_EXEMPLO = [
    "Quanto foi gasto por UF em 2025?",
    "Como variaram os gastos com passagens aéreas por mês em 2024?",
    "Quais categorias tiveram os maiores valores em 2025?",
    "Quanto foi gasto no total em 2024?",
]
PERGUNTA_INVALIDA = "A pergunta precisa ter entre 5 e 500 caracteres."
EM_ANDAMENTO = "Consultando os dados…"
CONCLUIDO = "Concluído"
NAO_CONCLUIDO = "Não foi possível concluir"


def escapar(texto: str) -> str:
    """Evita que valores em reais ("R$ 10 e R$ 20") virem fórmula LaTeX no markdown."""
    return texto.replace("$", r"\$")


def linha_do_passo(passo: PassoAgente) -> str:
    icone = "✅" if passo.sucesso else "❌"
    resultado = passo.saida if passo.sucesso else passo.erro
    duracao = f"{passo.duracao_ms / 1000:.1f}".replace(".", ",")
    return f"{icone} {passo.descricao}: {resultado} ({duracao} s)"


def desenhar_passo(passo: PassoAgente) -> None:
    st.markdown(escapar(linha_do_passo(passo)))
    if sql := passo.entrada.get("sql"):
        st.code(sql, language="sql")


def executar(texto: str) -> None:
    final = None
    with st.status(EM_ANDAMENTO, expanded=True) as status:
        for evento in cliente.perguntar(texto):
            if isinstance(evento, cliente.PassoRecebido):
                desenhar_passo(evento.passo)
            else:
                final = evento
        concluiu = isinstance(final, cliente.RespostaRecebida)
        status.update(
            label=CONCLUIDO if concluiu else NAO_CONCLUIDO,
            state="complete" if concluiu else "error",
        )


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
