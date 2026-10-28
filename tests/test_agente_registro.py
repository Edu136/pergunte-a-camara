import json

from src.agent.agente import Agente
from src.agent.registro import RegistroJSONL
from src.config import Settings
from tests.test_agente import SQL_CAT, SQL_UF, ConsultorFalso, LLMRoteirizado, sql, texto


def test_h6_cada_passo_vira_uma_linha_json(tmp_path):
    caminho = tmp_path / "logs" / "agente.jsonl"
    llm = LLMRoteirizado(sql("DROP TABLE despesas"), sql(SQL_UF), texto("Pronto."))
    agente = Agente(llm=llm, consultor=ConsultorFalso([]), config=Settings(_env_file=None),
                    registro=RegistroJSONL(caminho))

    agente.responder("Quanto por UF?")

    linhas = [json.loads(linha) for linha in caminho.read_text(encoding="utf-8").splitlines()]
    assert len(linhas) == 2
    assert linhas[0]["id_pergunta"] == linhas[1]["id_pergunta"]
    assert all(linha["pergunta"] == "Quanto por UF?" and linha["timestamp"] for linha in linhas)
    assert linhas[0]["sucesso"] is False and linhas[0]["erro"]
    assert linhas[1]["entrada"] == {"sql": SQL_UF} and linhas[1]["duracao_ms"] >= 0


def test_registro_acrescenta_sem_apagar(tmp_path):
    caminho = tmp_path / "agente.jsonl"
    registro = RegistroJSONL(caminho)
    llm = LLMRoteirizado(sql(SQL_UF), texto("a"), sql(SQL_CAT), texto("b"))
    agente = Agente(llm=llm, consultor=ConsultorFalso([], []), config=Settings(_env_file=None),
                    registro=registro)

    agente.responder("Pergunta um")
    agente.responder("Pergunta dois")

    assert len(caminho.read_text(encoding="utf-8").splitlines()) == 2
