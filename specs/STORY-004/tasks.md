# Tasks: STORY-004 — API `POST /perguntar` com os passos do agente em tempo real (SSE)

> **Story**: [story.md](story.md)
> **Spec**: [spec.bdd.md](spec.bdd.md)

## Tasks

### Task 1: Aviso de passo no agente

- **Cenários BDD**: H4, E3
- **Tipo**: feature
- **Dependência**: —
- **Critério de conclusão**: `responder(pergunta, ao_passo=None)`; helper `_anotar(passo)` concentra
  append + registro + aviso (remove os dois `if self.registro` duplicados) (RN9); testes das
  STORY-001 a 003 verdes
- **Status**: ⏳ Pendente

### Task 2: Gerador de eventos SSE

- **Cenários BDD**: H2, E2, E5, X2, X3 (no nível do gerador)
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: `eventos(agente, texto)` síncrono, com o agente numa thread daemon e
  ponte por `queue.Queue`; item final sempre posto no `finally`; `_sse(evento, json)` (RN1, RN2,
  RN5, RN8)
- **Status**: ⏳ Pendente

### Task 3: Endpoint `POST /perguntar` e montagem do agente

- **Cenários BDD**: H1, H3, H5, E1, E4, X1, X2, X3 (ponta a ponta via `TestClient`)
- **Tipo**: feature
- **Dependência**: Task 2
- **Critério de conclusão**: `StreamingResponse` com os headers da RN7; `obter_agente` com cache e
  `RegistroJSONL` (RN6); 422 sem chamar o agente (RN4)
- **Status**: ⏳ Pendente

### Task 4: Documentação, verificação manual e sync

- **Cenários BDD**: — (CA9 manual)
- **Tipo**: docs
- **Dependência**: Tasks 1–3
- **Critério de conclusão**: docstring de `src/api/main.py` atualizada; spec 01 cita o endpoint;
  roadmap marca o item; `curl -N` com Ollama e Postgres reais mostrando os passos chegando aos
  poucos e o `/health` respondendo durante a pergunta; ruff e pytest verdes
- **Status**: ⏳ Pendente

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4
```

## Progresso

- Total: 4 tasks
- Concluídas: 0/4
- Cenários BDD cobertos: 0/13 (H1–H5, E1–E5, X1–X3; outlines contam como 1)
