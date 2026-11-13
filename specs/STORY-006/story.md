# Story: STORY-006 — Conjunto de avaliação rotulado por categoria

## Descrição

Como **autor do projeto (AI Engineer)**,
Quero **um conjunto fixo de perguntas rotuladas por categoria, cada uma com o comportamento esperado
do agente (SQL de referência ou recusa)**,
Para que **o harness do bloco 3 meça acurácia de execução, recusa correta e bloqueio de injection
sempre sobre a mesma base, e eu compare modelos e versões do prompt com números, não impressões**.

## Contexto

Primeiro item do bloco 3 do [roadmap](../ROADMAP.md). O núcleo do agente está pronto (blocos 1 e 2),
mas nada mede se ele acerta. A Constituição exige métrica publicada para qualquer capacidade de IA
aparecer como pronta (princípio 10) e define FF-005 (acurácia de execução ≥ 80%) e FF-006 (0 números
sem lastro). As duas dependem deste conjunto.

Esta story entrega **só o conjunto e a validação dele**. O harness que roda o agente e calcula
métricas é o próximo item do roadmap.

Princípios em jogo:
- **P1 (neutralidade):** perguntas de opinião esperam recusa neutra. As perguntas do conjunto não
  citam deputados pelo nome.
- **P2 (fidelidade):** o SQL de referência é o gabarito. O resultado dele é o que o agente precisa
  reproduzir.
- **P3 (segurança):** todo SQL de referência passa pelo `sql_guard` e roda com `agente_leitura`.
- **Princípio 10:** exemplos de few-shot (bloco 4) nunca vêm deste conjunto.

## Critérios de Aceite

- [ ] **CA1 — Seis categorias:** o conjunto tem perguntas das categorias `facil`, `media`, `dificil`,
      `fora_do_escopo`, `opiniao` e `injection`, com pelo menos 5 perguntas em cada uma.
- [ ] **CA2 — Formato versionado e validado:** o conjunto fica num arquivo versionado no repositório.
      Cada item tem id único, pergunta (5–500 caracteres, como a API), categoria e comportamento
      esperado. Um schema Pydantic valida o arquivo. Item inválido falha com mensagem que aponta o id.
- [ ] **CA3 — Gabarito para as respondíveis:** perguntas `facil`, `media` e `dificil` trazem o SQL de
      referência e esperam `respondida = true`. As de `fora_do_escopo`, `opiniao` e `injection`
      esperam `respondida = false` e não têm SQL.
- [ ] **CA4 — SQL de referência seguro:** todo SQL de referência passa pelo `sql_guard`, verificado
      por teste no CI (sem banco).
- [ ] **CA5 — SQL de referência executa:** um comando verifica, no banco carregado e com
      `agente_leitura`, que cada SQL de referência roda dentro do `statement_timeout` e devolve ao
      menos uma linha não nula. A saída lista quais falharam.
- [ ] **CA6 — Dificuldade com critério explícito:** a regra que separa `facil`, `media` e `dificil`
      está escrita (ex.: nº de filtros, agregação, junção, subconsulta ou janela) e cada pergunta
      respondível segue a regra.
- [ ] **CA7 — Sem vazamento:** nenhuma pergunta do conjunto aparece nas perguntas de exemplo da demo
      nem no prompt do agente. Um teste garante isso, e o few-shot do bloco 4 vai usar o mesmo teste.
- [ ] **CA8 — Casos conhecidos cobertos:** os problemas registrados na STORY-005 entram como
      perguntas (ranking de categorias que virou `LIMIT 1`, agregação por categoria em 2025).

## Estimativa

- **Tamanho**: M
- **Complexidade**: Média

## Dependências

| Tipo | Descrição | Status |
|------|-----------|--------|
| Story | STORY-001 (ingestão + `sql_guard`) | Concluída |
| Story | STORY-005 (perguntas de exemplo da demo, para o teste de vazamento) | Concluída (PR pendente) |
| Serviço | PostgreSQL com 2024–2025 carregados (só para o CA5) | Disponível localmente |

## Notas

- Fica para a análise:
  - formato do arquivo (JSONL, JSON ou YAML) e onde mora (`experiments/`, `src/eval/`, `tests/fixtures/`);
  - tamanho total (proposta inicial: ~60 perguntas, 10 por categoria);
  - se `injection` cobre só a pergunta direta ou também texto que tenta forçar SQL destrutivo;
  - como comparar resultados no harness (ordem de linhas, nomes de colunas, arredondamento):
    registrar aqui só o que afeta o formato do gabarito.
- Fora do escopo:
  - harness de avaliação, métricas e relatório (próximo item do bloco 3);
  - comparação de modelos e análise de erros;
  - guardrail de entrada (bloco 4): hoje o agente pode até responder uma pergunta de opinião; o
    conjunto só registra o que **deveria** acontecer;
  - conjunto de avaliação do RAG (bloco 5).
