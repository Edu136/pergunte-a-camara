import pytest
from pydantic import ValidationError

from src.schemas import Pergunta, Resposta


def test_pergunta_muito_curta_falha():
    with pytest.raises(ValidationError):
        Pergunta(texto="oi")


def test_resposta_nao_respondida_sem_dados():
    resposta = Resposta(pergunta="Qual o PIB?", explicacao="Fora do escopo.", respondida=False)
    assert resposta.dados == [] and resposta.sql is None


def test_passo_agente_tem_detalhes_com_padroes():
    from src.schemas import PassoAgente

    passo = PassoAgente(ferramenta="consultar_sql", descricao="Consulta ao banco")
    assert passo.entrada == {} and passo.saida is None and passo.erro is None
    assert passo.duracao_ms == 0 and passo.sucesso is True


def test_configuracao_do_agente_tem_padroes():
    from src.config import Settings

    config = Settings(_env_file=None)
    assert config.agente_max_correcoes == 2
    assert config.agente_linhas_para_llm == 50
    assert config.ollama_num_ctx == 8192
    assert config.agente_log_path == "logs/agente.jsonl"


def test_limite_de_barras_do_grafico_tem_padrao():
    from src.config import Settings

    assert Settings(_env_file=None).grafico_max_barras == 20
