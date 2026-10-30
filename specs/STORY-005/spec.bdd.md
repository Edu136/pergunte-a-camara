# Spec BDD: STORY-005 — Demo em Streamlit com os passos do agente em tempo real

> **Story**: [story.md](story.md) · **Análise**: [analysis.md](analysis.md) · **Fluxo**: [blueprint.mermaid](blueprint.mermaid)
> **Status**: Approved (sincronizada após TDD; /review pendente)
> **Autor**: Edu136
> **Revisores**: —

---

## Feature: Demo que pergunta à API e mostra o agente trabalhando

A página envia a pergunta para `POST /perguntar` e desenha cada passo assim que ele chega. No fim
mostra a resposta com explicação, gráfico, tabela, SQL, fontes e o aviso de conferência, ou uma
mensagem amigável se algo falhar.

### Regras de Negócio

1. **RN1 — Validação local:** a pergunta segue `Pergunta` (5–500 caracteres). Se for inválida, a
   página mostra `"A pergunta precisa ter entre 5 e 500 caracteres."` e não chama a API.
2. **RN2 — Perguntas de exemplo:** vêm da constante `PERGUNTAS_EXEMPLO` (3 a 5 itens). Cada uma é
   uma pergunta válida pela RN1, sem nome de deputado e sem adjetivo de juízo (P1). Clicar numa
   delas envia a pergunta.
3. **RN3 — Eventos do cliente:** `cliente.perguntar(texto, config)` devolve, na ordem:
   - zero ou mais `PassoRecebido(PassoAgente)`;
   - **exatamente um** evento final, `RespostaRecebida(Resposta)` ou `Falha(mensagem)`.

   Nunca lança exceção para quem chama.
4. **RN4 — Mensagens de falha** (sem detalhe técnico; o detalhe vai para o log):

   | Situação | Mensagem |
   |---|---|
   | Conexão recusada | `"A API não está respondendo em {API_URL}. Verifique se ela está rodando."` |
   | Timeout | `"A resposta demorou mais que o esperado. Tente novamente."` |
   | Status `422` | `"A pergunta não foi aceita pela API. Revise o texto e tente novamente."` |
   | Outro status, evento `erro`, stream sem evento final, JSON ou schema inválido | `"Não foi possível concluir a pergunta. Tente novamente."` |
5. **RN5 — Timeouts:** conexão em 5 s; leitura (tempo máximo entre eventos) em `DEMO_TIMEOUT_S`.
   O endereço vem de `API_URL`. Ambos estão na config.
6. **RN6 — Linha do passo:** `"{✅|❌} {descricao}: {saida ou erro} ({duração} s)"`. A duração é
   em segundos, com uma casa e vírgula decimal. Se o passo tiver `entrada.sql`, o SQL aparece logo
   abaixo, em bloco de código.
7. **RN7 — Status:**
   - `"Consultando os dados…"` (em andamento) enquanto a pergunta roda;
   - `"Concluído"` (complete) quando chega uma `Resposta`;
   - `"Não foi possível concluir"` (error) quando chega uma `Falha`.
8. **RN8 — Resposta respondida:** nesta ordem:
   - a explicação;
   - o gráfico, quando o tipo for `linha` ou `barra`;
   - a tabela de dados pt-BR (`montar_figura` tipo `tabela`), uma única vez;
   - o SQL;
   - as fontes como links;
   - o aviso `AVISO_FONTE` = `"Verifique na fonte oficial antes de usar estes números."`.
9. **RN9 — Resposta não respondida:** só a explicação, como aviso. Sem gráfico, tabela, SQL,
   fontes nem `AVISO_FONTE`.
10. **RN10 — Explicação segura:** o `$` da explicação é escapado (`\$`) para não virar LaTeX, e o
    HTML continua desligado.
11. **RN11 — Estado:** a última execução (pergunta, passos, evento final) fica em
    `st.session_state`. Reexecuções sem envio redesenham dali, sem chamar a API.

---

### Cenários — Happy Path

```gherkin
Scenario: H1 — Cliente converte o stream em eventos validados
  Given a API responde 200 com: passo (consultar_sql), passo (gerar_grafico), resposta
  When o cliente pergunta "Quanto foi gasto por UF em 2025?"
  Then recebe PassoRecebido, PassoRecebido e RespostaRecebida, nesta ordem
  And os objetos são PassoAgente e Resposta válidos
```

```gherkin
Scenario: H2 — Leitor de SSE separa os eventos
  Given o texto "event: passo\ndata: {...}\n\n: comentário\n\nevent: resposta\ndata: {...}\n\n"
  When o texto é lido
  Then devolve [("passo", "{...}"), ("resposta", "{...}")], ignorando o comentário
```

```gherkin
Scenario: H3 — Resposta com gráfico de barras
  Given o cliente devolve um passo e uma Resposta respondida com gráfico "barra", 2 linhas, SQL e fonte
  When o usuário envia "Quanto foi gasto por UF em 2025?"
  Then a página mostra a explicação, um gráfico de barras e uma tabela de dados
  And mostra o SQL em bloco de código, a fonte como link e o aviso "Verifique na fonte oficial antes de usar estes números."
  And o status termina como "Concluído"
```

```gherkin
Scenario: H4 — Gráfico do tipo tabela não duplica a tabela
  Given uma Resposta respondida com gráfico "tabela"
  When o usuário envia a pergunta
  Then a página mostra exatamente uma figura (a tabela de dados)
```

```gherkin
Scenario: H5 — Pergunta de exemplo é enviada ao clicar
  Given a página aberta
  When o usuário clica na primeira pergunta de exemplo
  Then o cliente é chamado com o texto dessa pergunta
```

```gherkin
Scenario: H6 — Passos desenhados com resultado, duração e SQL
  Given o cliente devolve o passo consultar_sql (saida "2 linhas", duracao_ms 1234, entrada.sql "SELECT …")
  And o passo gerar_grafico (saida "barra")
  When o usuário envia a pergunta
  Then o status mostra "✅ Consulta ao banco de dados: 2 linhas (1,2 s)" e o SQL em bloco de código
  And mostra a linha de "Escolha automática do gráfico" com "barra"
```

### Cenários — Edge Cases

```gherkin
Scenario: E1 — Cliente entrega cada evento assim que ele chega
  Given a API envia o primeiro passo e só depois o resto do stream
  When o primeiro evento do cliente é lido
  Then ele é o PassoRecebido, e o restante do corpo ainda não foi lido
```

```gherkin
Scenario: E2 — Valor único: só a tabela
  Given uma Resposta respondida sem gráfico e com 1 linha
  When o usuário envia a pergunta
  Then a página mostra a explicação e a tabela de dados, sem outro gráfico
```

```gherkin
Scenario: E3 — Resposta não respondida vira só aviso
  Given uma Resposta com respondida = false e explicação "Não foi possível responder com os dados disponíveis."
  When o usuário envia a pergunta
  Then a página mostra essa explicação como aviso
  And não mostra gráfico, tabela, SQL, fontes nem o aviso de fonte oficial
```

```gherkin
Scenario: E4 — Valores em reais não viram fórmula
  Given uma Resposta com explicação "MG gastou R$ 10,00 e SP R$ 20,00."
  When a página desenha a resposta
  Then o markdown exibido contém "R\$ 10,00" e "R\$ 20,00"
```

```gherkin
Scenario: E5 — Interagir com a página não refaz a pergunta
  Given uma pergunta já respondida na sessão
  When a página é reexecutada sem novo envio
  Then o cliente não é chamado de novo
  And a explicação, a tabela e os passos continuam na tela
```

```gherkin
Scenario: E6 — Perguntas de exemplo neutras e válidas
  When PERGUNTAS_EXEMPLO é verificada
  Then tem de 3 a 5 itens, todos com 5–500 caracteres
  And nenhum contém adjetivo de juízo ("absurdo", "abusivo", "suspeito", "irregular", "escandaloso", "desperdício", "exagerado")
```

```gherkin
Scenario: E7 — Timeouts e endereço vêm da config
  Given API_URL = "http://api.teste:9000" e DEMO_TIMEOUT_S = 123
  When o cliente pergunta
  Then a requisição vai para "http://api.teste:9000/perguntar"
  And usa timeout de conexão 5 s e de leitura 123 s
```

### Cenários — Error Cases

```gherkin
Scenario Outline: X1 — Falhas de transporte e de protocolo viram Falha amigável
  Given <situação>
  When o cliente pergunta
  Then os eventos são <antes> seguidos de uma única Falha com a mensagem <mensagem> da RN4
  And nenhuma exceção chega a quem chamou

  Examples:
    | situação                                    | antes        | mensagem              |
    | a API recusa a conexão                      | nenhum       | conexão recusada      |
    | a leitura estoura o timeout                 | nenhum       | timeout               |
    | a API responde 422                          | nenhum       | status 422            |
    | a API responde 500                          | nenhum       | genérica              |
    | o stream traz um passo e o evento erro      | 1 passo      | genérica              |
    | o stream traz um passo e termina sem final  | 1 passo      | genérica              |
    | o stream traz data com JSON inválido        | nenhum       | genérica              |
    | o stream traz um passo fora do schema       | nenhum       | genérica              |
```

```gherkin
Scenario: X2 — Pergunta inválida é barrada na página
  When o usuário envia "oi"
  Then a página mostra "A pergunta precisa ter entre 5 e 500 caracteres."
  And o cliente não é chamado
```

```gherkin
Scenario: X3 — Falha depois de um passo preserva o passo
  Given o cliente devolve um passo e depois Falha("Não foi possível concluir a pergunta. Tente novamente.")
  When o usuário envia a pergunta
  Then a página mostra a mensagem de falha como erro
  And a linha do passo continua no status, que termina como "Não foi possível concluir"
  And não mostra tabela, SQL nem aviso de fonte
```

---

## Checklist de Qualidade

- [x] Cada cenário é independente
- [x] Cada cenário é determinístico (`httpx.MockTransport` e cliente falso no `AppTest`, sem rede)
- [x] Cada cenário é verificável (pytest)
- [x] Happy path, edge cases e error cases cobertos
- [x] Linguagem de domínio
- [x] Critérios de aceite da story mapeados:
  - CA1 → X2
  - CA2 → H5, E6
  - CA3 → H6, E1 + verificação manual do tempo real
  - CA4 → H3, H4, E2, E4
  - CA5 → E3
  - CA6 → X1, X3
  - CA7 → E7
  - CA8 → H1, H2, E1, X1 (cliente sem Streamlit)
  - CA9 → E5
