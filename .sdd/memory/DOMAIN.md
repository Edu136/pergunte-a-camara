# Domínio do Projeto

> Gerado por `/init`. Assistentes de IA: consulte para entender o domínio.
> Schema físico: `db/init.sql`.

## Entidades

| Entidade | Campos principais | Descrição |
|----------|------------------|-----------|
| Deputado | id (= ideCadastro = id da API), nome, partido atual, UF atual, legislatura, url_foto | Cadastro com a situação **mais recente**. Pode trocar de partido/UF e ter despesas em mais de uma legislatura. Tabela `deputados`. |
| Despesa | id_documento, deputado_id, nome_parlamentar, partido e UF na época, ano, mês, categoria, subcategoria, fornecedor, cnpj_fornecedor, data_emissao, valor_documento, valor_glosa, valor_liquido, url_documento | Linha da CEAP. `valor_liquido` = documento − glosa. Pode ser negativa (compensação de bilhete). `deputado_id` nulo em despesas de liderança. Nem toda tem nota digitalizada. Duplicatas exatas descartadas. Tabela `despesas`. |
| Fornecedor | nome, CNPJ | **Derivado** das despesas (sem tabela própria). Só PJ é identificado; CPF nunca armazenado (CNPJ nulo nesse caso). |
| Categoria de despesa | descrição, subcategoria opcional | Definida pela Câmara; o sistema não cria nem renomeia. Dimensão base da detecção de anomalias. Atributo de `despesas`. |
| Norma da CEAP | fonte (nome + link do ato), trecho, embedding (384d) | Base do RAG sobre o que pode ser reembolsado; toda resposta baseada nela cita a fonte. Tabela `documentos`. |

### Relacionamentos

- Deputado 1 — N Despesa (`despesas.deputado_id`, opcional).
- Despesa N — 1 Fornecedor (por nome/CNPJ, derivado).
- Despesa N — 1 Categoria (por descrição, derivado).
- Norma da CEAP não se relaciona por chave com as demais; é consultada por similaridade.

### Fora das entidades

- **Pergunta/Resposta**: contrato de entrada e saída da API (`src/schemas.py`: pergunta, SQL, dados,
  gráfico, explicação, fontes, passos). Não persistida; o contexto de conversa vive só na sessão.
- **Exemplo de few-shot** (pergunta → SQL): dado de apoio ao agente, não entidade de domínio.
  Nunca sobrepõe o conjunto de avaliação.

## Fluxos principais

> Escopo e ordem em `specs/ROADMAP.md`.

- Ingestão anual da CEAP: [a definir em /feature] — ver `specs/02-ingestao.md`
- Pergunta → guardrail de entrada → agente → ferramentas → guardrail de saída → resposta: [a definir em /feature] — ver `specs/01-agente-consultas.md`
- Avaliação (SQL, guardrails, RAG, comparação de modelos): [a definir em /feature]
- Ingestão e busca em normas (RAG híbrido + reranking): [a definir em /feature]
- Detecção de anomalias: [a definir em /feature]
- Ferramentas via servidor MCP: [a definir em /feature]

## Fronteiras externas

| Tipo | Nome | Descrição |
|------|------|-----------|
| Download HTTP | CEAP `camara.leg.br/cotas/Ano-{ano}.csv.zip` | Despesas anuais; cache em `data/raw/`, `--forcar-download` |
| API REST | Dados Abertos `/api/v2/deputados` | Cadastro e foto; opcional (`--sem-fotos`) |
| API HTTP local | Ollama | LLM `qwen2.5:7b` (comparação: `qwen2.5-coder:7b`); alternativa paga `gpt-4o-mini` via `LLM_PROVIDER` |
| DB | PostgreSQL 16 + pgvector (Docker) | Dados de despesas, deputados e normas |
| Lib local | sentence-transformers | Embeddings `paraphrase-multilingual-MiniLM-L12-v2` e reranking |
| Lib local | scikit-learn | Isolation Forest para anomalias |
| Tracing | Langfuse (Docker) | Observabilidade do agente |
| Protocolo | Servidor MCP | Expõe as ferramentas a clientes MCP |
