# Spec BDD: STORY-004 — API `POST /perguntar` com os passos do agente em tempo real (SSE)

> **Story**: [story.md](story.md) · **Análise**: [analysis.md](analysis.md) · **Fluxo**: [blueprint.mermaid](blueprint.mermaid)
> **Status**: Draft
> **Autor**: Edu136
> **Revisores**: —

---

## Feature: Pergunta por HTTP com passos em tempo real

O cliente envia uma pergunta para `POST /perguntar` e recebe, por Server-Sent Events, cada passo do
agente assim que ele termina, seguido da resposta final, ou de um erro genérico se algo imprevisto
acontecer.

### Regras de Negócio

1. **RN1 — Formato do evento:** cada evento é `event: <nome>\ndata: <json numa linha>\n\n`, com
   `<nome>` ∈ {`passo`, `resposta`, `erro`}. O `data` de `passo` é um `PassoAgente`, o de `resposta`
   é uma `Resposta` e o de `erro` é `{"mensagem": "..."}`. JSON em UTF-8, sem escapar acentos.
2. **RN2 — Ordem:** zero ou mais `passo`, na ordem de execução, seguidos de **exatamente um** evento
   final (`resposta` ou `erro`). Depois do evento final o stream é encerrado.
3. **RN3 — Coerência:** a lista `passos` do evento `resposta` é igual, na ordem, aos `passo` já
   enviados.
4. **RN4 — Entrada:** o corpo é validado por `Pergunta` (`texto`, 5–500 caracteres). Se for
   inválido, a API devolve `422` antes de chamar o agente.
5. **RN5 — Erro inesperado:** uma exceção não prevista vira o evento `erro` com a mensagem fixa
   `"Erro inesperado ao processar a pergunta."`, sem stack trace, SQL ou texto da exceção. O
   detalhe vai para o log do servidor (`log.exception`).
6. **RN6 — Agente da API:** uma única instância (`obter_agente`, com cache), montada com o LLM e o
   consultor de leitura da config e com `RegistroJSONL(AGENTE_LOG_PATH)`. Os testes a substituem
   por dependency override.
7. **RN7 — Headers:** `Content-Type: text/event-stream`, `Cache-Control: no-cache` e
   `X-Accel-Buffering: no`.
8. **RN8 — Execução:** o agente roda numa thread separada da que consome os eventos, e o gerador
   de eventos é síncrono (iterado no threadpool), então o event loop fica livre.
9. **RN9 — Aviso de passo:** `Agente.responder(pergunta, ao_passo=None)` chama `ao_passo(passo)`
   para cada passo, logo depois de registrá-lo no JSONL. Sem `ao_passo`, o comportamento é o de
   antes.

---

### Cenários — Happy Path

```gherkin
Scenario: H1 — Pergunta respondida vira stream de passos e resposta
  Given um agente cujo modelo consulta gastos por UF, o banco devolve 2 linhas e o modelo explica
  When o cliente envia POST /perguntar com {"texto": "Quanto cada UF gastou em 2025?"}
  Then o status é 200 e os headers seguem a RN7
  And os eventos são, nesta ordem: passo (consultar_sql), passo (gerar_grafico), resposta
  And a resposta tem respondida = true, o SQL executado, 2 linhas em dados e a fonte CEAP
```

```gherkin
Scenario: H2 — Passo é enviado antes de o agente terminar
  Given um agente que conclui um passo e depois fica parado esperando liberação
  When o primeiro evento do gerador de eventos é lido
  Then ele é o passo, recebido enquanto o agente ainda está parado
  And depois da liberação o próximo evento é a resposta
```

```gherkin
Scenario: H3 — Resposta final repete os passos enviados
  Given o stream de H1
  When os eventos passo e a resposta são comparados
  Then resposta.passos é igual, na ordem, à lista de passos enviados
```

```gherkin
Scenario: H4 — Agente avisa cada passo depois de registrá-lo
  Given um agente com registro e um callback ao_passo, e um modelo que faz uma consulta e responde
  When o agente responde
  Then ao_passo recebeu, na ordem, os mesmos passos de Resposta.passos
  And cada passo foi registrado no JSONL antes de ser avisado
```

```gherkin
Scenario: H5 — Agente da API grava o JSONL
  Given a configuração com AGENTE_LOG_PATH
  When obter_agente é chamado
  Then o agente tem um RegistroJSONL apontando para AGENTE_LOG_PATH
```

### Cenários — Edge Cases

```gherkin
Scenario Outline: E1 — Recusas e falhas conhecidas terminam com resposta não respondida
  Given um agente em que <situação>
  When o cliente envia uma pergunta válida
  Then o status é 200
  And os eventos são <passos> seguidos de um único evento resposta
  And a resposta tem respondida = false e explicacao = <mensagem>

  Examples:
    | situação                                   | passos                          | mensagem               |
    | o modelo responde sem consultar            | nenhum                          | SEM_DADOS              |
    | o LLM está indisponível                    | nenhum                          | LLM_FORA               |
    | o banco cai na consulta                    | 1 passo com sucesso = false     | BANCO_FORA             |
    | o modelo excede AGENTE_MAX_PASSOS          | AGENTE_MAX_PASSOS passos        | LIMITE_PASSOS          |
    | o modelo erra o SQL além das correções     | passos com sucesso = false      | CORRECOES_ESGOTADAS    |
```

```gherkin
Scenario: E2 — Acentos chegam intactos e cada data ocupa uma linha
  Given uma resposta cuja explicação tem "Despesas com divulgação" e uma quebra de linha
  When o evento resposta é emitido
  Then o data é uma única linha de JSON que contém "divulgação" sem escape \u
  And ao ser decodificado devolve a explicação original, com a quebra de linha
```

```gherkin
Scenario: E3 — Sem callback, o agente funciona como antes
  Given um agente sem ao_passo
  When o agente responde a uma pergunta com uma consulta
  Then a Resposta é a mesma que antes da STORY-004 (testes da STORY-001 a 003 seguem verdes)
```

```gherkin
Scenario: E4 — Uma única instância do agente
  When obter_agente é chamado duas vezes
  Then devolve o mesmo objeto (o cache de categorias vale entre perguntas)
```

```gherkin
Scenario: E5 — Agente roda fora da thread que consome os eventos
  Given um agente falso que anota a thread em que responder é executado
  When os eventos são consumidos até o fim
  Then a thread anotada é diferente da thread que consumiu os eventos
  And o gerador de eventos é um gerador síncrono
```

### Cenários — Error Cases

```gherkin
Scenario Outline: X1 — Corpo inválido é barrado antes do agente
  Given um agente falso que registra se foi chamado
  When o cliente envia POST /perguntar com <corpo>
  Then o status é 422, a resposta não é text/event-stream e o agente não foi chamado

  Examples:
    | corpo                         |
    | {}                            |
    | {"texto": "oi"}               |
    | {"texto": "<501 caracteres>"} |
    | um JSON malformado            |
```

```gherkin
Scenario: X2 — Exceção inesperada depois de um passo
  Given um agente que conclui um passo e então lança RuntimeError("detalhe interno SELECT secreto")
  When o cliente envia uma pergunta válida
  Then os eventos são: passo, erro
  And o erro tem mensagem "Erro inesperado ao processar a pergunta."
  And nenhum evento contém "detalhe interno", "SELECT secreto" nem "Traceback"
  And o log do servidor registrou a exceção com o detalhe
```

```gherkin
Scenario: X3 — Exceção inesperada antes de qualquer passo
  Given um agente que lança exceção logo ao começar
  When o cliente envia uma pergunta válida
  Then o único evento é erro, com a mensagem genérica, e o stream é encerrado
```

---

## Checklist de Qualidade

- [x] Cada cenário é independente
- [x] Cada cenário é determinístico (agentes falsos; sincronização por `threading.Event`, sem `sleep`)
- [x] Cada cenário é verificável (pytest, sem Ollama nem Postgres)
- [x] Happy path, edge cases e error cases cobertos
- [x] Linguagem de domínio
- [x] Critérios de aceite da story mapeados: CA1 H1 · CA2 H2 · CA3 H3 · CA4 X1 · CA5 E1 · CA6 X2, X3 · CA7 H4, H5 · CA8 todos (override) · CA9 E5 + verificação manual
