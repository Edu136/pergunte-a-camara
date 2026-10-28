import pytest
from pydantic import ValidationError

from src.schemas import Pergunta, Resposta


def test_pergunta_muito_curta_falha():
    with pytest.raises(ValidationError):
        Pergunta(texto="oi")


def test_resposta_nao_respondida_sem_dados():
    resposta = Resposta(pergunta="Qual o PIB?", explicacao="Fora do escopo.", respondida=False)
    assert resposta.dados == [] and resposta.sql is None
