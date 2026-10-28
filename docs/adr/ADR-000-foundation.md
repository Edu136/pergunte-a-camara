# ADR-000: Fundação do projeto

> **Data**: 2026-10-28
> **Status**: Accepted
> **Story**: —
> **Decisores**: eduardo.correa

## Contexto

O Pergunte à Câmara é um projeto de portfólio para o processo seletivo genAI (perfil AI Engineer).
Ele precisa demonstrar engenharia de agentes com tool use, Text-to-SQL seguro e avaliação de LLM
sobre dados reais da CEAP (2024–2025), com custo zero, execução local e um único desenvolvedor.
O escopo é completo e sem versões ([roadmap](../../specs/ROADMAP.md)): também guardrails, RAG,
detecção de anomalias, observabilidade e servidor MCP.

Os maiores riscos são: SQL malicioso gerado por prompt injection (R1), número errado atribuído a
um deputado real (R2), leitura política do projeto (R3) e CPF de pessoa física na fonte (R4).

## Opções Consideradas

### Opção A: Framework de agente (LangChain / LangGraph / Pydantic AI)

- **Prós**: menos código de orquestração; integrações prontas.
- **Contras**: esconde o funcionamento do tool use, que é a competência a demonstrar; mais
  dependências e abstração para depurar; menos controle sobre teto de passos e autocorreção.

### Opção B: Loop de agente próprio sobre a API de tool calling do Ollama

- **Prós**: mecanismo explícito e explicável; poucas dependências; controle total do teto de
  passos, da autocorreção do SQL e do registro de cada passo.
- **Contras**: mais código próprio para manter; sem recursos prontos de memória/grafos.

## Decisão

Escolhemos **Opção B** e a stack abaixo:

| Camada | Escolha | Motivação |
|--------|---------|-----------|
| Linguagem | Python 3.11 | Ecossistema de IA e dados |
| LLM | Ollama local, `qwen2.5:7b` (comparação `qwen2.5-coder:7b`) | Custo zero; suporte a tool calling. Troca para `gpt-4o-mini` só via `LLM_PROVIDER`, com limite de gasto prévio |
| Agente | Loop próprio (httpx + Pydantic) | Ver opções acima |
| Banco | PostgreSQL 16 + pgvector (Docker Compose) | `statement_timeout`, roles e busca vetorial no mesmo banco |
| Segurança SQL | `sql_guard` (sqlglot) + role `agente_leitura` | Duas camadas independentes (P3) |
| Embeddings | sentence-transformers, `paraphrase-multilingual-MiniLM-L12-v2` (384d) | Local, multilíngue, custo zero; também reranking (cross-encoder) |
| Anomalias | Estatística (z-score/IQR) + Isolation Forest (scikit-learn) | Local; comparação dentro da categoria |
| API / Demo | FastAPI (SSE) · Streamlit · Plotly | Contrato HTTP com streaming + demo que mostra passos, SQL e gráfico |
| Integração | Servidor MCP | Ferramentas reutilizáveis fora da demo, com as mesmas proteções |
| Observabilidade | Log JSONL dos passos + Langfuse auto-hospedado (Docker) | Mesmo dado serve à demo, ao tracing e à avaliação |
| Qualidade | pytest + ruff no GitHub Actions (push/PR) | Sensores automáticos para um time solo |

Padrões adotados (ver `.sdd/PROJECT-CONSTITUTION.md`): princípios P1–P4 (neutralidade,
fidelidade, segurança em duas camadas, LGPD), valor líquido como medida, Guard Clause/Fail Fast,
DTOs Pydantic, logging estruturado e mínimo de abstração.

Escopo: entrega contínua, sem versões nem data, na ordem de `specs/ROADMAP.md`. A avaliação é
construída logo após o núcleo do agente, para que cada capacidade seguinte seja medida antes de
virar destaque.

## Consequências

### Positivas

- O mecanismo do agente fica visível no código e na demo, reforçando o objetivo do portfólio.
- Nenhum custo recorrente; tudo roda com `docker compose up` + Ollama.
- A segurança não depende só do LLM nem só do validador.

### Negativas

- Um modelo 7B local pode errar SQL complexo e ser lento sem GPU (R6).
- O loop próprio precisa de testes para cobrir o que um framework já traria.
- O projeto fica preso a Postgres (dialeto do `sql_guard` e do prompt).

### Riscos

- SQL ruim do modelo local → autocorreção (até 2 tentativas), schema e exemplos no prompt, comparação de modelos na avaliação.
- Fluxo do agente crescer além de um loop simples → reavaliar LangGraph/Pydantic AI em novo ADR.

## Referências

- `specs/01-agente-consultas.md`, `specs/02-ingestao.md`
- `.sdd/PROJECT-CONSTITUTION.md`
