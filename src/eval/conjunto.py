"""Conjunto de avaliação: perguntas rotuladas por categoria com o comportamento esperado do agente.

Regras em specs/STORY-006/spec.bdd.md. O gabarito é SQL, nunca número escrito à mão (P2): o harness
roda o SQL de referência e o do agente no mesmo banco e compara os resultados.
"""

import ast
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Literal

import sqlglot
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator
from sqlglot import exp

from src.schemas import Pergunta
from src.tools.sql_guard import validar_sql

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_CONJUNTO = RAIZ / "experiments" / "conjunto_avaliacao.json"
CAMINHO_DEMO = RAIZ / "app" / "streamlit_app.py"

Categoria = Literal["facil", "media", "dificil", "fora_do_escopo", "opiniao", "injection"]
PREFIXOS: dict[str, str] = {
    "facil": "F", "media": "M", "dificil": "D",
    "fora_do_escopo": "X", "opiniao": "O", "injection": "I",
}
RESPONDIVEIS = {"facil", "media", "dificil"}
MAX_CONDICOES_FACIL = 2


class ConjuntoInvalido(ValueError):
    pass


def _parse(sql: str) -> exp.Expression:
    try:
        return sqlglot.parse_one(sql, read="postgres")
    except sqlglot.errors.ParseError as erro:
        raise ValueError(f"sql com erro de sintaxe: {erro}") from erro


class ItemAvaliacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[FMDXOI]\d{2}$")
    categoria: Categoria
    pergunta: str
    respondida: bool
    sql: str | None = None
    ordem_importa: bool = False
    nota: str | None = None

    @field_validator("pergunta")
    @classmethod
    def _pergunta_aceita_pela_api(cls, texto: str) -> str:
        return Pergunta(texto=texto).texto

    @model_validator(mode="after")
    def _consistente(self) -> "ItemAvaliacao":
        if self.id[0] != PREFIXOS[self.categoria]:
            raise ValueError(f"id de {self.categoria} começa com {PREFIXOS[self.categoria]}")
        if self.categoria in RESPONDIVEIS:
            if not self.respondida or not self.sql:
                raise ValueError(f"{self.categoria} exige respondida = true e sql preenchido")
            validar_sql(self.sql)  # SQLInvalido é ValueError: vira erro do item (RN6)
            consulta = _parse(self.sql)
            if self.ordem_importa and consulta.args.get("order") is None:
                raise ValueError("ordem_importa = true exige ORDER BY no sql")
        elif self.respondida or self.sql is not None or self.ordem_importa:
            raise ValueError(
                f"{self.categoria} exige respondida = false, sql = null e ordem_importa = false"
            )
        return self


def _rotulo(bruto: object, posicao: int) -> str:
    id_ = bruto.get("id") if isinstance(bruto, dict) else None
    return f"Item {id_}" if isinstance(id_, str) and id_ else f"Item na posição {posicao}"


def _motivos(erro: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" if e["loc"] else e["msg"]
        for e in erro.errors()
    )


def carregar_conjunto(caminho: Path | str = CAMINHO_CONJUNTO) -> list[ItemAvaliacao]:
    caminho = Path(caminho)
    if not caminho.is_file():
        raise ConjuntoInvalido(f"Arquivo do conjunto não encontrado: {caminho}")
    try:
        brutos = json.loads(caminho.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as erro:
        raise ConjuntoInvalido(f"Conjunto de avaliação com JSON inválido: {erro}") from erro
    if not isinstance(brutos, list):
        raise ConjuntoInvalido("Conjunto de avaliação com JSON inválido: a raiz precisa ser lista")

    itens = []
    for posicao, bruto in enumerate(brutos, start=1):
        try:
            itens.append(ItemAvaliacao.model_validate(bruto))
        except ValidationError as erro:
            raise ConjuntoInvalido(f"{_rotulo(bruto, posicao)}: {_motivos(erro)}") from erro

    repetidos = sorted(id_ for id_, n in Counter(i.id for i in itens).items() if n > 1)
    if repetidos:
        raise ConjuntoInvalido(f"Ids repetidos: {', '.join(repetidos)}")
    return itens


# --- dificuldade (RN7) -------------------------------------------------------------------------


def classificar_dificuldade(sql: str) -> str:
    consulta = _parse(sql)
    aninhada = any(select is not consulta for select in consulta.find_all(exp.Select))
    if aninhada or consulta.find(exp.Join, exp.Window, exp.CTE):
        return "dificil"
    if consulta.args.get("group") or consulta.args.get("order"):
        return "media"
    onde = consulta.args.get("where")
    condicoes = len(list(onde.this.flatten())) if onde and isinstance(onde.this, exp.And) else 1
    return "facil" if condicoes <= MAX_CONDICOES_FACIL else "media"


# --- vazamento (RN8) ---------------------------------------------------------------------------


def normalizar(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(re.sub(r"[^\w\s]", " ", sem_acento.lower()).split())


def vazamentos(perguntas: list[str], referencias: list[str]) -> list[str]:
    """Perguntas que aparecem (normalizadas, por palavra inteira) em algum texto de referência."""
    alvos = [f" {normalizar(r)} " for r in referencias]
    return [p for p in perguntas if any(f" {normalizar(p)} " in alvo for alvo in alvos)]


def perguntas_exemplo_da_demo(caminho: Path | str = CAMINHO_DEMO) -> list[str]:
    """Lê PERGUNTAS_EXEMPLO da página por ast: importar a página executaria o Streamlit."""
    arvore = ast.parse(Path(caminho).read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Assign) and any(
            isinstance(alvo, ast.Name) and alvo.id == "PERGUNTAS_EXEMPLO" for alvo in no.targets
        ):
            return list(ast.literal_eval(no.value))
    raise LookupError(f"PERGUNTAS_EXEMPLO não encontrada em {caminho}")
