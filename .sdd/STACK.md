# Stack

> Detectada no código e confirmada no `/init` (2026-10-28).

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.11 |
| API | FastAPI + uvicorn |
| Demo | Streamlit + Plotly |
| Config / validação | pydantic v2 + pydantic-settings (`.env`) |
| Banco | PostgreSQL 16 + pgvector (`pgvector/pgvector:pg16`, Docker Compose) · psycopg 3 |
| SQL guard | sqlglot |
| LLM | Ollama (`qwen2.5:7b`) via httpx · OpenAI opcional (`LLM_PROVIDER`) |
| Embeddings | sentence-transformers (384d) |
| Dados | pandas |
| Testes / lint | pytest · ruff (E, F, I, UP, B; linha 100) |
| CI | GitHub Actions (push e PR) |
