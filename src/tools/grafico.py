"""Escolha automática do gráfico a partir dos dados da resposta (ADR-002) e figura Plotly.

Regras em specs/STORY-003/spec.bdd.md e fluxo em specs/STORY-003/blueprint.mermaid.
"""

import re
from typing import Any

from src.schemas import Grafico

COLUNAS_DE_TEMPO = {"ano", "mes"}
CONTAGEM = re.compile(r"quantidade|qtd|count|numero|^n_|^total_\w+s$")

# Série única: slot 1 da paleta de referência da skill dataviz (validada); grade recessiva.
COR_SERIE = "#2a78d6"
COR_GRADE = "rgba(128, 128, 128, 0.2)"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")
TITULO_TABELA = "Resultado da consulta"
ROTULOS = {
    "valor_liquido": "Valor líquido",
    "valor_documento": "Valor do documento",
    "valor_glosa": "Valor glosado",
    "uf": "UF",
    "mes": "Mês",
    "ano": "Ano",
}

Dados = list[dict[str, Any]]


def rotulo(coluna: str) -> str:
    if coluna in ROTULOS:
        return ROTULOS[coluna]
    texto = coluna.replace("_", " ")
    return texto[:1].upper() + texto[1:]


def _primeiro_valor(dados: Dados, coluna: str) -> Any:
    return next((linha[coluna] for linha in dados if linha.get(coluna) is not None), None)


def _eh_tempo(coluna: str, valor: Any) -> bool:
    return (
        coluna in COLUNAS_DE_TEMPO
        or coluna.startswith("data")
        or (isinstance(valor, str) and bool(DATA_ISO.match(valor)))
    )


def _eh_id(coluna: str) -> bool:
    return coluna == "id" or coluna.endswith("_id")


def _eh_medida(coluna: str, valor: Any) -> bool:
    numero = isinstance(valor, int | float) and not isinstance(valor, bool)
    return numero and not _eh_tempo(coluna, valor) and not _eh_id(coluna)


def _tabela(colunas: list[str], medidas: list[str]) -> Grafico:
    eixo_y = medidas[0] if medidas else colunas[0]
    return Grafico(tipo="tabela", eixo_x=colunas[0], eixo_y=eixo_y, titulo=TITULO_TABELA)


def _grafico(tipo: str, eixo_x: str, eixo_y: str) -> Grafico:
    return Grafico(tipo=tipo, eixo_x=eixo_x, eixo_y=eixo_y,
                   titulo=f"{rotulo(eixo_y)} por {rotulo(eixo_x)}")


def escolher_grafico(dados: Dados, max_barras: int) -> Grafico | None:
    if not dados:
        return None

    colunas = list(dados[0])
    valores = {coluna: _primeiro_valor(dados, coluna) for coluna in colunas}
    medidas = [c for c in colunas if _eh_medida(c, valores[c])]
    dimensoes = [c for c in colunas if c not in medidas]
    tempos = [c for c in dimensoes if _eh_tempo(c, valores[c])]

    if not medidas:
        return _tabela(colunas, medidas)
    if not dimensoes:
        return None if len(dados) == 1 else _tabela(colunas, medidas)

    if set(dimensoes) == COLUNAS_DE_TEMPO:
        um_ano = len({linha["ano"] for linha in dados}) == 1
        if um_ano and len(dados) >= 2:
            return _grafico("linha", "mes", medidas[0])
        return _tabela(colunas, medidas)

    if len(dimensoes) != 1:
        return _tabela(colunas, medidas)

    dimensao = dimensoes[0]
    if dimensao in tempos:
        if len(dados) >= 2:
            return _grafico("linha", dimensao, medidas[0])
    elif len(dados) <= max_barras:
        return _grafico("barra", dimensao, medidas[0])
    return _tabela(colunas, medidas)


def _eh_contagem(coluna: str) -> bool:
    return bool(CONTAGEM.search(coluna))


def _pt_br(numero: float, casas: int) -> str:
    return f"{numero:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _coluna_formatada(dados: Dados, coluna: str) -> list[Any]:
    """Valores da coluna como texto pt-BR (o go.Table ignora layout.separators)."""
    valores = [linha.get(coluna) for linha in dados]
    if not _eh_medida(coluna, _primeiro_valor(dados, coluna)):
        return valores
    if _eh_contagem(coluna):
        return [None if v is None else _pt_br(v, 0) for v in valores]
    # Espaço sem quebra: o "R$" não fica sozinho numa linha da célula.
    return [None if v is None else f"R$ {_pt_br(v, 2)}" for v in valores]


def montar_figura(grafico: Grafico, dados: Dados):
    """Figura Plotly para a demo: série única, R$ e separadores pt-BR (RN9)."""
    import plotly.graph_objects as go

    colunas = list(dados[0]) if dados else []
    if grafico.tipo == "tabela":
        figura = go.Figure(go.Table(
            header={"values": [rotulo(c) for c in colunas], "align": "left"},
            cells={"values": [_coluna_formatada(dados, c) for c in colunas], "align": "left"},
        ))
        figura.update_layout(title=grafico.titulo, separators=",.")
        return figura

    x = [linha.get(grafico.eixo_x) for linha in dados]
    y = [linha.get(grafico.eixo_y) for linha in dados]
    em_reais = not _eh_contagem(grafico.eixo_y)
    prefixo = "R$ " if em_reais else ""
    dica = f"%{{x}}<br>{prefixo}%{{y:,.{2 if em_reais else 0}f}}<extra></extra>"

    if grafico.tipo == "linha":
        serie = go.Scatter(
            x=x, y=y, mode="lines+markers", hovertemplate=dica,
            line={"color": COR_SERIE, "width": 2, "shape": "linear"},
            marker={"color": COR_SERIE, "size": 8},
        )
    else:
        serie = go.Bar(x=x, y=y, hovertemplate=dica, marker={"color": COR_SERIE})

    figura = go.Figure(serie)
    figura.update_layout(
        title=grafico.titulo,
        separators=",.",
        showlegend=False,
        bargap=0.35,
        barcornerradius=4,
        hovermode="x unified" if grafico.tipo == "linha" else "closest",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 8, "r": 8, "t": 48, "b": 8},
    )
    figura.update_xaxes(title=rotulo(grafico.eixo_x), showgrid=False)
    if grafico.tipo == "barra":
        # Ids e outros códigos numéricos são categorias, não uma escala contínua.
        figura.update_xaxes(type="category")
    if grafico.eixo_x == "ano":
        figura.update_xaxes(dtick=1, tickformat="d")
    if grafico.eixo_x == "mes":
        figura.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=MESES)
    # Eixo a partir de zero: um eixo cortado exagera variações (neutralidade, P1).
    figura.update_yaxes(
        title=rotulo(grafico.eixo_y), tickprefix=prefixo, tickformat="~s", rangemode="tozero",
        gridcolor=COR_GRADE, gridwidth=1, zeroline=True, zerolinecolor=COR_GRADE,
    )
    return figura
