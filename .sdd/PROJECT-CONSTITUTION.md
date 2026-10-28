# Constituição: Pergunte à Câmara

> Gerada em: 2026-10-28 | Versão: 1.1
> Gerada por: `/init` — SDD Kit
> Fonte de verdade dos princípios P1–P4 (antes em `specs/00-principios.md`).
> Em conflito com `.sdd/CONSTITUTION.md` (framework), a lei universal prevalece.

---

## 1. Identidade

| Campo | Valor |
|-------|-------|
| **Projeto** | Pergunte à Câmara |
| **Problema** | "Quero saber como os deputados federais usam a cota parlamentar perguntando em português — sem baixar planilhas, saber SQL ou analisar dados — e receber números oficiais, gráfico e a origem de cada informação para conferir." |
| **Usuário principal** | Cidadão curioso (respostas curtas + gráfico) e jornalista de dados (quer o SQL e o link da nota). Secundário: estudante/pesquisador. Local, 1 usuário por vez, dezenas de perguntas/dia. |
| **Tipo** | Projeto de portfólio (AI Engineer) que reúne num só produto o leque de IA aplicada: agente com tool use, Text-to-SQL seguro, guardrails, RAG, ML para anomalias, avaliação de LLM, observabilidade e MCP. Uso público é objetivo secundário. |
| **Horizonte** | Entrega contínua, sem versões nem data. Escopo completo e ordem de construção em [`specs/ROADMAP.md`](../specs/ROADMAP.md). |

**Restrições rígidas:** custo zero (modelos locais, dados abertos; API paga só opcional e com limite prévio) · execução local, sem nuvem · somente dados oficiais da Câmara.

---

## 2. Lei do Domínio

1. **P1 — Neutralidade** — O agente descreve dados, não julga. Pedido de opinião/juízo sobre deputado ou partido → `respondida = false` (barrado já no guardrail de entrada). Rankings só por valor e sem adjetivos ("maiores valores em X"). Toda anomalia exibe literalmente: *"valor fora do padrão estatístico; não indica irregularidade"*. Demo e post não citam deputados pelo nome.
2. **P2 — Fidelidade** — Todo número exibido vem de uma consulta SQL executada *naquela resposta*; o LLM nunca produz valor. O guardrail de saída rejeita explicação com número ausente dos dados retornados. Toda resposta com dados traz o SQL e a fonte oficial; sem dados → o agente diz isso.
3. **P3 — Segurança em duas camadas** — Todo SQL gerado (pelo agente ou via MCP) passa pelo `sql_guard` (um comando, só `SELECT`, só tabelas permitidas, `LIMIT` obrigatório) **e** roda com o usuário `agente_leitura` (somente leitura, `statement_timeout` 5s). Uma camada nunca justifica afrouxar a outra.
4. **P4 — LGPD** — CPF de fornecedor pessoa física é descartado na ingestão: nunca persistido, logado, enviado ao tracing ou exibido. Só CNPJ é armazenado; caso contrário o campo fica nulo.
5. **Valor líquido é a medida** — Toda análise de gasto usa `valor_liquido` (documento − glosa). Valores negativos (compensação de bilhete) entram nas somas; nunca são filtrados.
6. **Partido/UF da época** — Agregações por partido ou UF usam os campos da `despesas` (situação no gasto), não o cadastro atual de `deputados`, salvo se a pergunta pedir a situação atual.
7. **Categorias pertencem à Câmara** — O sistema não cria, renomeia nem funde categorias. Comparações de valor (anomalias) só dentro da mesma categoria.
8. **Nada some na ingestão sem registro** — Despesas de liderança (`deputado_id` nulo) são mantidas; só duplicatas exatas são descartadas, e todo descarte aparece no relatório de limpeza da carga.
9. **Dados do banco são dados, não instruções** — Resultados de consulta e trechos de normas entram no prompt delimitados como dados. Nenhuma ferramenta (agente ou MCP) escreve no banco.
10. **Capacidade de IA só é destaque se for medida** — Nenhuma capacidade aparece como pronta no README sem teste e métrica publicada em `experiments/`. Exemplos de few-shot nunca vêm do conjunto de avaliação.
11. **Conversa vive só na sessão** — O contexto para perguntas de acompanhamento fica em memória da sessão; perguntas e respostas não são persistidas no banco.

---

## 3. Mandatos de Qualidade

### Invioláveis (bloqueiam entrega)
- Suíte de comandos maliciosos do `sql_guard` 100% bloqueada; agente e servidor MCP só conhecem `DATABASE_URL_LEITURA`.
- Teste de ingestão garante que nenhum CPF chega ao banco.
- CI verde (ruff + pytest) e nenhum secret no código.

### Críticos (revisados em todo PR)
- Contrato `Resposta` sempre com SQL + fonte quando houver dados (P2); recusas neutras (P1).
- Ingestão (CEAP e normas) idempotente, valida a entrada e falha com mensagem clara.
- Todo passo do agente (ferramenta, entrada, saída, tempo, sucesso) registrado em JSONL e no tracing; teto `AGENTE_MAX_PASSOS` e até 2 autocorreções de SQL.
- Limites, modelos e limiares vêm de config (`.env`), nunca hardcoded.

### Desejáveis (metas, não bloqueadores)
- Acurácia de execução ≥ 80% no conjunto de avaliação.
- Metas de recall@k do RAG e de taxa de recusa correta: definidas após a primeira medição.

---

## 4. Técnicas Prioritárias

### Patterns a priorizar neste projeto
| Pattern | Razão |
|---------|-------|
| Guard Clause / Fail Fast (1.6, 5.1) | `sql_guard`, guardrails e validação das ingestões: rejeitar cedo, com motivo explícito. |
| DTO com Pydantic (1.5) | `Resposta`, `PassoAgente` e entradas/saídas das ferramentas: contrato validado na fronteira LLM ↔ código. |
| Erro de domínio tipado (5.4) | Erros do SQL viram mensagem estruturada devolvida ao agente para autocorreção. |
| Logging estruturado (5.5) | JSONL dos passos alimenta demo, tracing e avaliação. |
| Strategy (1.3) | `LLM_PROVIDER` e modelos trocáveis só por configuração (base da comparação de modelos). |
| Retry com backoff (5.6) | Chamadas ao Ollama e à API da Câmara. |
| Menor privilégio (6.12) + A03 Injection | Núcleo do risco R1, inclusive no servidor MCP. |
| Teste de fronteira (4.6) | `LIMIT`, timeout, teto de passos, valores negativos, grounding. |

### Anti-patterns críticos neste contexto
| Anti-pattern | Risco específico |
|-------------|-----------------|
| Over-engineering / Abstração prematura (2.10, 2.5) | Framework de agente ou camadas extras escondem a competência a demonstrar. |
| God Function (2.1) | Loop do agente acumulando prompt, guardrails, parsing, execução e log numa função só. |
| Magic Numbers (2.8) | Limites de segurança e limiares espalhados no código em vez de `config.py`. |

---

## 5. Fronteiras e Integrações

| Sistema | Tipo | Responsabilidade | Risco |
|---------|------|-----------------|-------|
| CEAP `camara.leg.br/cotas/Ano-{ano}.csv.zip` | Download HTTP | Despesas por ano (cache em `data/raw/`) | Mudança de formato, duplicatas, CPF na fonte |
| API Dados Abertos `/api/v2/deputados` | API REST | Cadastro e foto (opcional, `--sem-fotos`) | Indisponibilidade; não pode bloquear a carga |
| Atos oficiais da CEAP | Download | Normas para o RAG | Formato (PDF/HTML) e versão vigente |
| Ollama (`qwen2.5:7b`, `qwen2.5-coder:7b`) | API HTTP local | Tool calling, SQL, guardrails, juiz da avaliação | SQL errado, lentidão sem GPU, falha de tool call |
| PostgreSQL 16 + pgvector | DB (Docker) | Despesas, deputados, normas, exemplos de few-shot | Consulta cara (timeout), privilégio indevido |
| sentence-transformers / scikit-learn | Libs locais | Embeddings 384d, reranking, Isolation Forest | Divergência com `EMBEDDING_DIM`; modelos pesados na RAM |
| Langfuse (Docker) | Tracing | Observabilidade do agente | Vazar dado sensível no trace (P4) |
| Clientes MCP | Protocolo MCP | Uso das ferramentas fora da demo | Mesma superfície de injection do agente (P3) |

---

## 6. Acordos do Time

- **Time**: 1 dev (solo).
- **Nível de abstração**: mínimo necessário. Loop de agente próprio; módulos por responsabilidade (`ingestion`, `tools`, `agent`, `guardrails`, `rag`, `eval`, `api`, `mcp`), sem camadas de repositório/serviço até a regra de três exigir.
- **Revisão de código**: `/review` antes de todo merge na `main`; PR mesmo solo, para o CI rodar.
- **Decisões arquiteturais**: ADR curto ao adicionar uma capacidade de IA com dependência nova, trocar dependência central, mexer em segurança (P3/P4) ou mudar o contrato `Resposta`.
- **Frequência de /sync**: ao concluir cada bloco do roadmap.

---

## 7. Emendas

| # | Data | Mudança | Razão |
|---|------|---------|-------|
| 1 | 2026-10-28 | Fim das versões (v1/v1.1/v2) e do prazo; escopo completo em `specs/ROADMAP.md`; princípios 10 e 11; guardrails, RAG híbrido, Langfuse e MCP no escopo. | Decisão do autor: projeto completo em entrega contínua, sem data. |

---

## 8. Fitness Functions

| # | Função | Limiar | Sensor | Frequência |
|---|--------|--------|--------|------------|
| FF-001 | Comandos maliciosos bloqueados pelo `sql_guard` | 100% | `tests/test_sql_guard.py` | CI |
| FF-002 | Lint | 0 erros | `ruff check .` | CI |
| FF-003 | CPF na saída da ingestão | 0 ocorrências | teste de `transform` | CI |
| FF-004 | Código do agente/ferramentas/MCP usando conexão de escrita | 0 referências a `DATABASE_URL` (só `_LEITURA`) | constraint test | CI |
| FF-005 | Acurácia de execução no conjunto de avaliação | ≥ 80% | harness de avaliação | ao fechar bloco do roadmap |
| FF-006 | Respostas com número ausente dos dados | 0 no conjunto de avaliação | guardrail de saída + harness | ao fechar bloco do roadmap |
| FF-007 | Drift spec ↔ código | 0 cenários desincronizados | `/sync` | ao fechar bloco do roadmap |
