"""Registro dos passos do agente em JSONL: uma linha por chamada de ferramenta.

O mesmo dado alimenta a demo, o tracing e a avaliação.
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from src.schemas import PassoAgente


class RegistroJSONL:
    def __init__(self, caminho: str | Path):
        self.caminho = Path(caminho)

    def registrar(self, id_pergunta: str, pergunta: str, passo: PassoAgente) -> None:
        linha = {
            "id_pergunta": id_pergunta,
            "pergunta": pergunta,
            "timestamp": datetime.now(UTC).isoformat(),
            **passo.model_dump(),
        }
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.caminho.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(linha, ensure_ascii=False, default=str) + "\n")
