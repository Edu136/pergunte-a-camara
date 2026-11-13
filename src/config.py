"""Configurações do projeto, lidas do arquivo .env."""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://camara:camara@localhost:5432/camara"
    database_url_leitura: str = "postgresql://agente_leitura:leitura@localhost:5432/camara"

    camara_api_url: str = "https://dadosabertos.camara.leg.br/api/v2"
    camara_cotas_url: str = "https://www.camara.leg.br/cotas/Ano-{ano}.csv.zip"
    anos: str = "2024,2025"

    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dim: int = 384

    llm_provider: Literal["ollama", "openai"] = "ollama"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ollama_num_ctx: int = 8192
    ollama_timeout_s: float = 300
    ollama_keep_alive: str = "30m"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    sql_limite_linhas: int = 200
    sql_timeout_ms: int = 5000
    agente_max_passos: int = 6
    agente_max_correcoes: int = 2
    agente_linhas_para_llm: int = 50
    agente_log_path: str = "logs/agente.jsonl"

    grafico_max_barras: int = 20

    api_url: str = "http://127.0.0.1:8000"
    demo_timeout_s: float = 900

    @property
    def lista_anos(self) -> list[int]:
        return [int(a) for a in self.anos.split(",") if a.strip()]


settings = Settings()
