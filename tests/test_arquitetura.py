"""Fitness function FF-004: agente, ferramentas e cliente de LLM só usam a conexão de leitura."""

import re
from pathlib import Path

import pytest

PASTAS_DO_AGENTE = ["src/agent", "src/tools", "src/llm"]
CONEXAO_DE_ESCRITA = re.compile(r"database_url(?!_leitura)", re.IGNORECASE)


def _arquivos():
    raiz = Path(__file__).resolve().parent.parent
    return [arquivo for pasta in PASTAS_DO_AGENTE for arquivo in (raiz / pasta).rglob("*.py")]


def test_detector_reconhece_a_conexao_de_escrita():
    assert CONEXAO_DE_ESCRITA.search("psycopg.connect(settings.database_url)")
    assert CONEXAO_DE_ESCRITA.search("os.environ['DATABASE_URL']")
    assert not CONEXAO_DE_ESCRITA.search("settings.database_url_leitura")


@pytest.mark.parametrize("arquivo", _arquivos(), ids=lambda a: a.name)
def test_codigo_do_agente_nao_usa_conexao_de_escrita(arquivo):
    assert not CONEXAO_DE_ESCRITA.search(arquivo.read_text(encoding="utf-8"))
