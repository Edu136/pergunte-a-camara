"""Contratos de entrada e saída do agente (definidos em specs/01-agente-consultas.md)."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Pergunta(BaseModel):
    texto: str = Field(min_length=5, max_length=500)


class PassoAgente(BaseModel):
    """Um passo do raciocínio do agente, exibido em tempo real na interface (ADR-001)."""

    ferramenta: str
    descricao: str
    entrada: dict[str, Any] = {}
    saida: str | None = None
    erro: str | None = None
    duracao_ms: int = 0
    sucesso: bool = True


class Grafico(BaseModel):
    tipo: Literal["barra", "linha", "pizza", "tabela"]
    eixo_x: str
    eixo_y: str
    titulo: str


class Resposta(BaseModel):
    pergunta: str
    sql: str | None = None
    dados: list[dict[str, Any]] = []
    grafico: Grafico | None = None
    explicacao: str
    fontes: list[str] = []
    passos: list[PassoAgente] = []
    respondida: bool = True
