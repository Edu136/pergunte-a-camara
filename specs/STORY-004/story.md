# Story: STORY-004 — API `POST /perguntar` com os passos do agente em tempo real (SSE)

## Descrição

Como **cidadão curioso ou jornalista de dados (por meio da demo)**,
Quero **enviar uma pergunta e acompanhar cada passo do agente enquanto ele acontece, até a resposta
final**,
Para que **eu entenda como o número foi obtido (que SQL rodou, quantas linhas voltaram) e não fique
olhando uma tela parada durante os segundos que o modelo local leva para responder**.

## Contexto

Item do bloco 2 do [roadmap](../ROADMAP.md). O agente (STORY-001), a validação de categorias
(STORY-002) e o gráfico (STORY-003) já montam a `Resposta` completa, mas só no fim: hoje
`Agente.responder` devolve os passos de uma vez, dentro de `Resposta.passos`. A API em
`src/api/main.py` tem apenas o `/health`. Esta story expõe o agente por HTTP e entrega cada
`PassoAgente` como evento Server-Sent Events assim que ele é concluído. A demo em Streamlit, que vai
consumir esse stream, é uma story separada.

Princípios em jogo: P2 (a resposta final é a mesma `Resposta` do agente, com SQL e fonte), P1
(recusas e falhas com mensagem neutra), mandato crítico de registro dos passos em JSONL (continua
valendo quando a pergunta chega pela API).

## Critérios de Aceite

- [ ] **CA1 — Pergunta vira stream:** `POST /perguntar` com `{"texto": "..."}` válido responde
      `200` com `Content-Type: text/event-stream`. O stream tem um evento `passo` por `PassoAgente`,
      na ordem de execução, e termina com um único evento `resposta` com a `Resposta` completa.
- [ ] **CA2 — Passo chega quando acontece:** cada evento `passo` é enviado logo que o passo termina,
      antes de o agente chegar à resposta final, e não acumulado para o fim.
- [ ] **CA3 — Contrato coerente:** cada evento `passo` segue o schema `PassoAgente`, e a lista
      `passos` do evento `resposta` é igual, na mesma ordem, aos passos já enviados.
- [ ] **CA4 — Entrada inválida é barrada antes do agente:** um corpo sem `texto`, ou com texto fora
      de 5–500 caracteres, recebe `422`, sem stream e sem chamar o agente.
- [ ] **CA5 — Recusas e falhas conhecidas são respostas:** LLM fora, banco fora, limite de passos,
      autocorreções esgotadas e falta de dados terminam com o evento `resposta` e
      `respondida = false`, com a mensagem neutra do agente. O status continua `200`.
- [ ] **CA6 — Erro inesperado não vaza detalhes:** uma exceção não prevista dentro do agente gera um
      evento `erro` com mensagem genérica, sem stack trace, SQL ou detalhes internos, e o stream é
      encerrado. O detalhe completo vai só para o log do servidor.
- [ ] **CA7 — Registro mantido:** perguntas feitas pela API continuam gravando cada passo no JSONL,
      como na STORY-001.
- [ ] **CA8 — Testável sem infraestrutura:** o agente usado pelo endpoint pode ser substituído nos
      testes (dependency override do FastAPI), sem precisar de Ollama nem de Postgres.
- [ ] **CA9 — Servidor não trava:** como o agente é síncrono, executá-lo não bloqueia o event loop:
      o `/health` responde enquanto uma pergunta está em andamento.

## Estimativa

- **Tamanho**: M
- **Complexidade**: Média

## Dependências

| Tipo | Descrição | Status |
|------|-----------|--------|
| Story | STORY-001 (agente e `Resposta`) | Concluída |
| Story | STORY-003 (gráfico na `Resposta`) | Concluída |
| Biblioteca | FastAPI + uvicorn (`requirements.txt`) | Disponível |

## Notas

- Fica para a análise: como o agente avisa cada passo (callback/observador junto do `Registro`,
  ou `responder` virando gerador), se usamos `sse-starlette` ou `StreamingResponse` puro, e se o
  stream deve expor o `id_pergunta` do JSONL.
- Fica para a análise: o que fazer quando o cliente desconecta no meio (interromper o agente ou
  deixá-lo terminar e registrar).
- Fora do escopo: autenticação, rate limit e CORS para origens externas. A execução é local e com
  1 usuário (Constituição §1). Endpoint síncrono sem stream: só se a demo precisar.
