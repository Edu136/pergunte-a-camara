# Memória do Projeto

> Assistentes de IA: leia este arquivo ANTES de qualquer ação.
> Lei do projeto: `.sdd/PROJECT-CONSTITUTION.md`.

## Identificação

- **Projeto**: Pergunte à Câmara
- **Cliente**: projeto pessoal de portfólio (processo seletivo genAI, perfil AI Engineer)

## Contexto

Agente de IA que responde, em português, perguntas sobre como os deputados federais usam a Cota
para o Exercício da Atividade Parlamentar (CEAP). Cada resposta traz números oficiais vindos de SQL
executado no banco, um gráfico, o SQL e a fonte para o usuário conferir. Atende o cidadão curioso e o
jornalista de dados, sem exigir planilhas ou SQL. Roda 100% local e com custo zero (Ollama + Postgres
via Docker). O objetivo principal é demonstrar, num só produto, o leque de IA aplicada: agente com
tool use, Text-to-SQL seguro, guardrails, RAG, anomalias, avaliação de LLM, observabilidade e MCP.
Entrega contínua, sem versões nem data — escopo em `specs/ROADMAP.md`.

## Convenções

- **Branch**: `{type}/{story-id}-{descricao}`
- **Commits**: Conventional Commits
- **Testes**: Todo cenário BDD = pelo menos 1 teste automatizado (pytest); lint com ruff (py311, linha 100)
- **Idioma**: código, specs e mensagens em português (ex.: `consultar_sql`, `PassoAgente`)
- **Specs existentes**: `specs/NN-nome.md` (00 princípios → ponteiro para a Constituição, 01 agente, 02 ingestão)

## Glossário

| Termo | Significado |
|-------|-------------|
| CEAP | Cota para o Exercício da Atividade Parlamentar — verba reembolsada aos deputados |
| Despesa | Uma linha do CSV anual da CEAP (um documento fiscal reembolsado) |
| Valor líquido | Valor do documento − glosa; medida usada em todas as análises |
| Glosa | Parte do valor do documento não reembolsada pela Câmara |
| Compensação de bilhete | Despesa com valor negativo referente a bilhete aéreo; entra nas somas |
| Liderança | Liderança partidária; tem despesas próprias com `deputado_id` nulo |
| ideCadastro | Id do deputado no CSV; igual ao id da API de Dados Abertos |
| Legislatura | Período de mandato; um deputado pode ter despesas em mais de uma |
| Norma da CEAP | Ato oficial que define o que pode ser reembolsado (base do RAG) |
| Guardrail de entrada | Classificador que barra perguntas fora do escopo, de opinião ou com injection antes do agente |
| Guardrail de saída (grounding) | Verificação de que todo número da explicação existe nos dados retornados |
| Few-shot dinâmico | Exemplos pergunta→SQL recuperados por similaridade e injetados no prompt |
| Busca híbrida | Combinação de busca vetorial (pgvector) e full-text (Postgres) no RAG |
| Reranking | Reordenação dos trechos recuperados por um cross-encoder local |
| LLM-as-judge | LLM local que avalia a fidelidade de respostas do RAG |
| `sql_guard` | 1ª camada de segurança: valida o SQL gerado (sqlglot) |
| `agente_leitura` | 2ª camada: role Postgres somente leitura com `statement_timeout` 5s |
| Passo do agente | Uma chamada de ferramenta registrada (`PassoAgente`), exibida na demo e logada em JSONL |
| Acurácia de execução | % de perguntas do conjunto de avaliação cujo SQL retorna o resultado esperado |
| Anomalia | Valor fora do padrão estatístico dentro de uma categoria; não indica irregularidade |

## Links

- Repositório: https://github.com/Edu136/pergunte-a-camara
- Board: 
- Docs: `README.md`, `specs/`, `docs/adr/`
