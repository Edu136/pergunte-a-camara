# Roadmap — escopo completo

> Sem versões nem datas: entrega contínua. Cada capacidade entra quando estiver **pronta, testada e
> avaliada** (Constituição, princípio 10). A ordem abaixo é a ordem de construção: cada bloco usa o
> anterior, e a avaliação vem cedo para medir tudo o que vier depois.

## 1. Fundação de dados

- [x] **Ingestão da CEAP** (2024–2025): download, limpeza, descarte de CPF, relatório, carga idempotente por ano. → [spec 02](02-ingestao.md)
- [x] **`sql_guard`**: um comando, só `SELECT`, tabelas permitidas, `LIMIT` obrigatório + usuário `agente_leitura`.

## 2. Núcleo do agente

- [x] **Loop de agente próprio com tool use** (Ollama, httpx, Pydantic): teto de passos, saídas estruturadas validadas por schema, registro de cada passo em JSONL. → [spec 01](01-agente-consultas.md)
- [x] **`consultar_sql`** com schema no prompt e **autocorreção** (até 2 tentativas a partir do erro do guard ou do banco).
- [x] **`gerar_grafico`**: escolhe o gráfico (linha, barra ou tabela) pelo formato dos dados, por regras fixas ([ADR-002](../docs/adr/ADR-002-grafico-por-regras.md)). → [STORY-003](STORY-003/spec.bdd.md)
- [x] **API `POST /perguntar`** com **streaming dos passos** (SSE). → [STORY-004](STORY-004/spec.bdd.md)
- [ ] **Demo em Streamlit**: passos em tempo real, SQL, gráfico, explicação, fontes e aviso "verifique na fonte oficial".

## 3. Avaliação (vem antes das demais capacidades de IA)

- [ ] **Conjunto de avaliação** com perguntas rotuladas por categoria: fácil, média, difícil, fora do escopo, pedido de opinião, tentativa de injection.
- [ ] **Harness de avaliação**: acurácia de execução do SQL, taxa de recusa correta, bloqueio de injection ponta a ponta, latência e passos por pergunta.
- [ ] **Comparação de modelos**: `qwen2.5:7b`, `qwen2.5-coder:7b` e, opcionalmente, `gpt-4o-mini` como referência de teto.
- [ ] **Análise de erros** publicada: onde e por que cada modelo erra.

## 4. Confiabilidade (guardrails)

- [ ] **Guardrail de entrada**: classifica a pergunta (dentro do escopo / fora / opinião / injection) antes do agente.
- [ ] **Guardrail de saída (grounding)**: todo número citado na explicação precisa existir nos dados retornados; senão a resposta é refeita ou rebaixada.
- [ ] **Few-shot dinâmico**: recupera por similaridade os exemplos pergunta→SQL mais próximos e os injeta no prompt (exemplos nunca vêm do conjunto de avaliação).

## 5. Conhecimento (RAG nas normas da CEAP)

- [ ] **Ingestão das normas**: download dos atos oficiais, chunking, embeddings locais (384d) em pgvector.
- [ ] **`buscar_normas`** com **busca híbrida** (vetorial + full-text do Postgres) e **reranking** com cross-encoder local; toda resposta cita a fonte.
- [ ] **Avaliação do RAG**: recall@k da recuperação e fidelidade da resposta (LLM-as-judge local) em um conjunto próprio.

## 6. Análise

- [ ] **`detectar_anomalias`**: estatística por categoria (z-score / IQR) e Isolation Forest, sempre com o aviso "valor fora do padrão estatístico; não indica irregularidade".
- [ ] **Mapa de gastos por UF** na demo.

## 7. Conversa

- [ ] **Memória de sessão**: perguntas de acompanhamento ("e em 2024?", "só MG") reaproveitam o contexto da conversa; nada é persistido.

## 8. Operação e integração

- [ ] **Observabilidade com Langfuse** auto-hospedado (Docker): trace de cada pergunta, ferramenta, tokens e latência.
- [ ] **Servidor MCP** expondo `consultar_sql`, `buscar_normas` e `detectar_anomalias` para clientes MCP (ex.: Claude Desktop), com as mesmas proteções do agente.

## 9. Vitrine

- [ ] README com GIF, tabela de resultados, análise de erros e "por que sem framework de agente".
- [ ] Modo demo com amostra pequena dos dados (sobe com poucos comandos, sem baixar os CSVs completos).
- [ ] Vídeo da demo e post no LinkedIn.

## Fora do escopo (e por quê)

| Item | Motivo |
|---|---|
| Fine-tuning de modelo | Sem GPU e com custo zero; few-shot dinâmico + avaliação entregam o mesmo aprendizado com menos risco. |
| Multiagente | Um agente com ferramentas resolve o problema; mais agentes só adicionam latência e pontos de falha. |
| Deploy em nuvem | Restrição de execução local e custo zero; a arquitetura não pode impedir, mas não é meta. |
| Dados do Senado e assembleias | Somente dados oficiais da Câmara dos Deputados. |
