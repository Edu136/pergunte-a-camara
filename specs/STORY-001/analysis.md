# Análise — STORY-001: Agente com SQL seguro e autocorreção

## 1. Código relevante

| Módulo | Situação | Uso nesta story |
|---|---|---|
| `src/tools/sql_guard.py` | Pronto | `validar_sql()` + `SQLInvalido`: 1ª camada; mensagem do erro alimenta a autocorreção |
| `src/config.py` | Pronto | `llm_provider`, `ollama_*`, `agente_max_passos`, `sql_limite_linhas`, `database_url_leitura` |
| `src/schemas.py` | Ampliar | `PassoAgente` precisa de entrada, saída, duração e erro (CA5) |
| `db/init.sql` | Pronto | Role `agente_leitura` (2ª camada) com `statement_timeout` 5s |
| `src/agent/`, `src/llm/` | Vazio / novo | Loop do agente, prompts e cliente de LLM |

**Padrões já em uso a seguir:**
- Injeção de dependência por parâmetro com padrão opcional (`baixar_cotas(..., cliente: httpx.Client | None)`).
- Testes de HTTP com `httpx.MockTransport` (sem rede) — serve para simular o Ollama.
- Funções puras separadas de I/O (`transform.py` × `load.py`).
- Nomes, mensagens e docstrings em português; erros como subclasses de exceções da stdlib.

## 2. Domínio

**Conceitos novos:** passo do agente, tentativa de correção, mensagem da conversa com o LLM,
definição de ferramenta. Nenhum é entidade de domínio (DOMAIN.md): são internos ao agente.

**Regras explícitas:** P2, P3, P9, CA1–CA9.

**Regras implícitas que precisam ficar escritas na spec:**
- **Qual SQL vai na `Resposta`:** o da *última* consulta bem-sucedida; todas as consultas ficam
  registradas em `passos`.
- **Resultado vazio é sucesso:** 0 linhas → `respondida = true`, explicação diz que não há registros.
- **Contagem da autocorreção:** falhas **consecutivas** de `consultar_sql`. Uma consulta bem-sucedida
  zera o contador. 1 tentativa + 2 correções = no máximo 3 falhas seguidas.
- **Fonte oficial fixa:** toda resposta com dados inclui a fonte da CEAP (`camara.leg.br/cotas`).
- **O prompt de sistema carrega as regras do domínio:** `valor_liquido` como medida, negativos nas
  somas, partido/UF da época, `deputado_id` nulo = liderança.

## 3. Direção estratégica

**Abordagem:** módulos novos, sem refactor prévio.

```
src/llm/        cliente.py   → Protocol ClienteLLM + criar_cliente(settings)
                ollama.py    → POST /api/chat com tools, stream=false, temperature 0
src/tools/      consultar_sql.py → valida (guard) + executa (conexão de leitura) + serializa
src/agent/      agente.py    → loop: LLM → ferramenta → resultado delimitado → LLM ... → Resposta
                prompts.py   → prompt de sistema (schema + regras + categorias) e formatação dos dados
                registro.py  → escrita dos passos em JSONL
```

**Decisões propostas:**

| # | Decisão | Recomendação | Alternativa |
|---|---|---|---|
| D1 | Argumento de `consultar_sql` | **O modelo escreve o SQL** (`consultar_sql(sql)`): 1 chamada ao LLM por passo, o erro volta naturalmente como resultado da ferramenta | Ferramenta recebe a sub-pergunta e chama outro LLM para gerar SQL (2 níveis, mais chamadas, mais lento num 7B) |
| D2 | Categorias no prompt | **Lista real via `SELECT DISTINCT categoria`** na criação do agente (cacheada) — o modelo precisa dos textos exatos da Câmara para filtrar | Só descrever a coluna (o modelo chuta os textos e erra filtros) |
| D3 | Terceira barreira barata | **Executar em transação `READ ONLY`** + `SET statement_timeout` a partir de `SQL_TIMEOUT_MS` (hoje fixo em 5s no role) | Confiar só no role |
| D4 | Funções perigosas no guard | **Bloquear funções `pg_*`, `dblink*`, `lo_*`** no `sql_guard` (hoje `SELECT pg_sleep(60)` e `SELECT pg_read_file(...)` passam pelo guard; o banco segura, mas P3 pede as duas camadas) | Deixar para o bloco de guardrails |
| D5 | Limites em config | Novos: `AGENTE_MAX_CORRECOES=2`, `AGENTE_LINHAS_PARA_LLM=50`, `OLLAMA_NUM_CTX=8192`, `AGENTE_LOG_PATH=logs/agente.jsonl` | Constantes no código (viola o mandato "limites vêm de config") |
| D6 | Provedor `openai` | `criar_cliente` lança erro claro "provedor não implementado" | Implementar já (fora do escopo) |

**Patterns (PLAYBOOK):** Strategy para `ClienteLLM` (1.3), DTO Pydantic para passos e respostas
(1.5), erro de domínio tipado — `LLMIndisponivel`, `SQLInvalido`, `ErroExecucaoSQL` (5.4), logging
estruturado (5.5), Guard Clause no loop (1.6). Sem framework, sem classe base abstrata além do Protocol.

**Mudança de contrato (ADR-001):** `PassoAgente` ganha `entrada`, `saida` (resumo), `duracao_ms` e
`erro`; e registra-se D1 (o LLM escreve o SQL). A tabela da spec 01 ("Gera SQL a partir da
pergunta") será ajustada para refletir D1.

**Fronteira de escopo:** nada de gráfico, API, demo, guardrails, few-shot, memória de conversa.

## 4. Riscos e edge cases

| Risco | Impacto | Mitigação nesta story |
|---|---|---|
| **Janela de contexto do Ollama** (padrão 2048–4096 tokens) estoura com schema + categorias + resultados | Alto: modelo "esquece" o schema silenciosamente | `OLLAMA_NUM_CTX` em `options`; no máximo `AGENTE_LINHAS_PARA_LLM` linhas devolvidas ao modelo |
| **Tool calling instável no 7B** (tool call vindo como texto JSON no `content`) | Médio | Tratado como resposta final sem consulta → CA3 (`respondida=false`). Frequência medida no bloco 3 |
| Várias tool calls numa mesma mensagem | Médio | Processar todas; cada uma conta como passo para o teto |
| Ferramenta desconhecida ou argumentos malformados | Médio | Erro devolvido ao modelo, conta como falha e como passo |
| Timeout do Postgres (`QueryCanceled`) | Médio | Mensagem orientando a agregar/filtrar; conta como falha corrigível |
| `Decimal`/`date` do psycopg não serializáveis | Baixo | Conversão explícita para `float`/ISO na saída da ferramenta |
| Explicação cita número fora dos dados | Alto (P2) | **Aceito por ora**: guardrail de saída é do bloco 4 (FF-006). Prompt instrui a usar só os dados |
| Resposta em inglês/chinês (Qwen) | Baixo | Prompt em português exigindo resposta em português; medido no bloco 3 |
| Não determinismo | Médio para avaliação | `temperature 0` e `seed` fixos |
| Ollama fora do ar | Médio | `LLMIndisponivel` com mensagem clara → `respondida=false` |
| Injection pela pergunta | Alto | Guard + role + `READ ONLY` (D3, D4); classificador de entrada é do bloco 4 |
