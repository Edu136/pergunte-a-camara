# Análise — STORY-004: API `POST /perguntar` com os passos do agente em tempo real (SSE)

## 1. Código relevante

| Módulo | Situação | Uso nesta story |
|---|---|---|
| `src/api/main.py` | Só `/health` | Recebe o endpoint `POST /perguntar` |
| `src/agent/agente.py` (`Agente.responder`) | Pronto, síncrono | Precisa avisar cada passo **durante** a execução; hoje só os devolve no fim |
| `src/agent/registro.py` (`RegistroJSONL`) | Pronto | Continua gravando cada passo (CA7); é montado junto com o agente da API |
| `src/schemas.py` (`Pergunta`, `PassoAgente`, `Resposta`) | Pronto | `Pergunta` valida a entrada (CA4); os outros dois viram o `data` dos eventos. **Contrato inalterado** |
| `src/llm/cliente.py` (`criar_cliente`), `src/tools/consultar_sql.py` (`ConsultorSQL`) | Prontos | Montagem do agente real na API |
| `tests/test_api.py` | Só `/health` | Recebe os testes do endpoint |
| `.github/workflows/ci.yml` | Já instala `fastapi` e `httpx` | Nada a ajustar, se não entrar dependência nova (ver D3) |

O agente chama `self.registro.registrar(...)` em **dois lugares** (o passo do gráfico e o passo de
cada ferramenta). Esse é o ponto natural para avisar o passo também ao stream.

## 2. Domínio

- Nenhum conceito novo de domínio: o stream só transporta `PassoAgente` e `Resposta`, que já existem.
- Regras explícitas:
  - O evento final é a mesma `Resposta` do agente (P2: SQL e fonte quando houver dados).
  - Recusas e falhas conhecidas já saem como `respondida = false` com mensagem neutra (P1).
  - Todo passo continua no JSONL (mandato crítico).
- Regra implícita: o agente **nunca lança exceção nos caminhos previstos**: LLM fora, banco fora,
  limite de passos e correções esgotadas viram `Resposta`. Portanto, um evento `erro` só aparece
  para bug ou falha não prevista, como erro de validação Pydantic ou de I/O do JSONL (CA6).
- `Pergunta.texto` (5–500 caracteres) já é a validação de entrada. Com ela no corpo, o FastAPI
  devolve `422` antes de o endpoint rodar (CA4), sem código extra.

## 3. Direção estratégica

### D1 — Como o agente avisa cada passo

| | **Callback opcional em `responder` (recomendado)** | `responder` vira gerador |
|---|---|---|
| Mudança no agente | `responder(pergunta, ao_passo=None)` + um helper `_anotar(passo)` que junta append, registro e aviso | Reescrever o loop com `yield` e devolver a `Resposta` como último item ou via `StopIteration.value` |
| Testes existentes | Intactos (a assinatura antiga continua válida) | Todos os que usam `responder` mudam |
| Uso sem stream (avaliação, MCP) | Igual ao de hoje | Precisa consumir o gerador inteiro |
| God Function | Diminui (o helper tira duplicação do registro) | Mantém o loop do mesmo tamanho |

**Recomendação:** callback. O `_anotar` concentra os dois `if self.registro` que hoje estão
duplicados.

### D2 — Agente síncrono × stream assíncrono (CA2, CA9)

O agente bloqueia (httpx síncrono no Ollama, psycopg síncrono). A ponte proposta:

1. O endpoint cria uma `queue.Queue` e roda `agente.responder(texto, ao_passo=fila.put)` numa
   `threading.Thread`.
2. Um **gerador síncrono** lê a fila e produz os eventos SSE: `passo`… e depois `resposta`, ou
   `erro` se a thread terminar com exceção.
3. `StreamingResponse` itera geradores síncronos no threadpool do Starlette, então o event loop fica
   livre e o `/health` responde durante uma pergunta (CA9).

O gerador fica numa função própria (`eventos(agente, texto)`), testável sem HTTP.

### D3 — Formato SSE: `StreamingResponse` puro × `sse-starlette`

**Recomendação:** `StreamingResponse` puro, com `media_type="text/event-stream"`. O formato
(`event: …\ndata: <json>\n\n`) cabe numa função de três linhas. Sem dependência nova, não precisa
de ADR nem de mudança no CI. O `sse-starlette` traz ping de keep-alive e detecção de desconexão,
que não fazem falta em execução local com 1 usuário (Constituição §1, anti-pattern 2.10).

Eventos:

| `event` | `data` | Quando |
|---|---|---|
| `passo` | `PassoAgente.model_dump_json()` | Cada passo concluído |
| `resposta` | `Resposta.model_dump_json()` | Fim normal (inclui `respondida = false`) |
| `erro` | `{"mensagem": "Erro inesperado ao processar a pergunta."}` | Exceção não prevista; detalhe só em `log.exception` |

Headers: `Cache-Control: no-cache` e `X-Accel-Buffering: no`. O segundo evita buffering se um
proxy for colocado na frente depois.

### D4 — Montagem do agente (CA8)

A dependência `obter_agente()` monta o `Agente` com `criar_cliente(settings)`, `ConsultorSQL()` e
`RegistroJSONL(settings.agente_log_path)`. Ela usa `lru_cache`, então existe uma instância só,
o que preserva o cache de categorias entre perguntas. Os testes trocam a dependência via
`app.dependency_overrides` por um agente com LLM e consultor falsos, como já fazem `test_agente.py`
e `test_agente_registro.py`.

### D5 — `id_pergunta` no stream

**Fora por ora (YAGNI).** Nem a demo nem a avaliação precisam dele, e expô-lo exigiria tirá-lo de
dentro de `responder`. Entra quando a observabilidade (Langfuse, bloco 8) precisar correlacionar
trace e log.

### D6 — Cliente desconecta no meio

**O agente termina e o log fica completo.** Não há como cancelar com segurança uma chamada httpx
síncrona já em curso no Ollama. A thread segue até o fim, grava o JSONL e descarta os eventos.
Com a thread `daemon=True`, ela não segura o desligamento do servidor.

### Estrutura

```
src/agent/agente.py   responder(pergunta, ao_passo=None); _anotar(passo) = append + registro + aviso
src/api/main.py       POST /perguntar(Pergunta) -> StreamingResponse(eventos(agente, texto))
                      obter_agente()  (dependência com lru_cache, sobrescrita nos testes)
                      eventos(agente, texto)  (gerador: thread + fila -> linhas SSE)
                      _sse(evento, json) -> "event: …\ndata: …\n\n"
```

O módulo é pequeno, então tudo fica em `main.py`. Se crescer (MCP e outros endpoints), extrair
`src/api/stream.py`.

## 4. Riscos e edge cases

| Risco | Mitigação |
|---|---|
| `TestClient` pode bufferizar o corpo inteiro e não provar o "tempo real" (CA2) | Provar o CA2 no gerador `eventos()`: um agente falso trava (`threading.Event`) depois do 1º passo, e o teste lê o 1º evento **antes** de liberá-lo. Pelo `TestClient`, testar só formato e ordem |
| CA9 (event loop livre) é difícil de testar de forma determinística | Garantido por construção (gerador síncrono no threadpool + agente em thread). Um teste checa que `eventos` é gerador síncrono e que o agente roda fora da thread chamadora. Verificação manual com `curl` documentada nas tasks |
| Exceção dentro da thread se perde | Capturar na thread, colocar um sentinela de erro na fila e fazer `log.exception` com o detalhe (CA6) |
| Exceção no callback (`fila.put`) | Fila sem limite: `put` não bloqueia nem falha |
| Gerador fica preso se a thread morrer sem avisar | A thread **sempre** termina com um item final, `resposta` ou `erro`, colocado num `finally`. O gerador para ao recebê-lo |
| Corrida no cache `_categorias` com duas perguntas simultâneas | Benigna: as duas leem as mesmas categorias, e a última atribuição vence. Não justifica lock |
| Duas perguntas ao mesmo tempo disputam o Ollama | Aceito (1 usuário). Sem fila global nesta story |
| JSON com acentos no `data` | `model_dump_json()` gera UTF-8 válido; o `data` é uma linha só (JSON não tem `\n` literal) |
| `Resposta.dados` grande (até `SQL_LIMITE_LINHAS` = 200 linhas) | Cabe num evento. Sem paginação |
