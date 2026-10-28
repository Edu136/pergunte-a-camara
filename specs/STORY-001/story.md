# Story: STORY-001 — Agente responde perguntas com SQL seguro e autocorreção

## Descrição

Como **cidadão curioso ou jornalista de dados**,
Quero **fazer uma pergunta em português sobre os gastos da cota parlamentar e receber a resposta
calculada a partir dos dados oficiais**,
Para que **eu tenha números confiáveis e veja exatamente qual consulta os produziu, sem saber SQL**.

## Contexto

Primeira capacidade do bloco 2 do [roadmap](../ROADMAP.md) — o coração do projeto. Implementa o loop
de agente próprio com tool use (ADR-000) e a ferramenta `consultar_sql`, apoiando-se no `sql_guard` e
no usuário `agente_leitura` já existentes. Detalha a [spec 01](../01-agente-consultas.md).

Fica **fora** desta story: `gerar_grafico`, endpoint `POST /perguntar`, demo, guardrails de
entrada/saída, few-shot dinâmico, memória de conversa e as demais ferramentas — cada uma tem story
própria no roadmap.

Princípios em jogo: P2 (fidelidade), P3 (segurança em duas camadas), P9 (dados não são instruções).

## Critérios de Aceite

- [ ] **CA1 — Resposta com dados:** para uma pergunta respondível, o agente chama `consultar_sql`, o SQL
      passa pelo `sql_guard`, é executado com o usuário somente leitura, e o agente devolve uma
      `Resposta` com `respondida = true`, o SQL executado, os dados retornados, uma explicação em
      português e a fonte oficial da CEAP em `fontes`.
- [ ] **CA2 — Autocorreção:** se o SQL for rejeitado pelo `sql_guard` ou falhar no banco (sintaxe,
      coluna inexistente, timeout), a mensagem de erro volta ao modelo, que pode corrigir em até
      **2 novas tentativas**. Esgotadas, a resposta sai com `respondida = false` e explicação do motivo.
- [ ] **CA3 — Sem dados, sem número:** se o agente encerrar sem nenhuma consulta bem-sucedida, a
      resposta sai com `respondida = false`, sem `sql` nem `dados` (P2).
- [ ] **CA4 — Teto de passos:** o agente nunca executa mais que `AGENTE_MAX_PASSOS` chamadas de
      ferramenta; ao atingir o teto, encerra com `respondida = false`.
- [ ] **CA5 — Passos rastreáveis:** cada chamada de ferramenta gera um `PassoAgente` (ferramenta,
      entrada, resumo da saída, duração, sucesso) na `Resposta` e uma linha no log JSONL.
- [ ] **CA6 — Dados delimitados:** os resultados do banco voltam ao modelo como dados delimitados,
      nunca concatenados como instrução (P9).
- [ ] **CA7 — Provedor por configuração:** o cliente de LLM é escolhido por `LLM_PROVIDER`; o provedor
      Ollama é implementado. Falha de comunicação com o LLM gera erro claro, não exceção crua.
- [ ] **CA8 — Testável sem infraestrutura:** toda a lógica do agente é testada com LLM e banco falsos;
      o CI roda sem Ollama e sem Postgres.
- [ ] **CA9 — Menor privilégio:** o agente só usa `DATABASE_URL_LEITURA` (FF-004).

## Estimativa

- **Tamanho**: G
- **Complexidade**: Alta

## Dependências

| Tipo | Descrição | Status |
|------|-----------|--------|
| Código | `src/tools/sql_guard.py` | Concluída |
| Código | `db/init.sql` (role `agente_leitura`) | Concluída |
| Código | Ingestão da CEAP (dados para teste manual) | Concluída |
| Serviço | Ollama com `qwen2.5:7b` (só para teste manual/avaliação) | Local |
| Serviço | PostgreSQL via Docker (só para teste manual/avaliação) | Local |

## Notas

- `PassoAgente` hoje tem só `ferramenta`, `descricao` e `sucesso`. O CA5 exige ampliá-lo — mudança no
  contrato `Resposta`, que pelos acordos do time gera ADR.
- Acurácia real com o modelo local não é critério desta story: é medida no bloco 3 (avaliação).
