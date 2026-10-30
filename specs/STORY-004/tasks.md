# Tasks: STORY-004 — API `POST /perguntar` com os passos do agente em tempo real (SSE)

> **Story**: [story.md](story.md)
> **Spec**: [spec.bdd.md](spec.bdd.md)

## Tasks

### Task 1: Aviso de passo no agente

- **Cenários BDD**: H4, E3
- **Tipo**: feature
- **Dependência**: —
- **Critério de conclusão**: `responder(pergunta, ao_passo=None)`; helper `anotar(passo)` concentra
  append + registro + aviso (remove os dois `if self.registro` duplicados) (RN9); testes das
  STORY-001 a 003 verdes
- **Status**: ✅ Concluída

### Task 2: Gerador de eventos SSE

- **Cenários BDD**: H2, E2, E5, X2, X3 (no nível do gerador)
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: `eventos(agente, texto)` síncrono, com o agente numa thread daemon e
  ponte por `queue.Queue`; item final sempre posto no `finally`; `_sse(evento, json)` (RN1, RN2,
  RN5, RN8)
- **Status**: ✅ Concluída

### Task 3: Endpoint `POST /perguntar` e montagem do agente

- **Cenários BDD**: H1, H3, H5, E1, E4, X1, X2, X3 (ponta a ponta via `TestClient`)
- **Tipo**: feature
- **Dependência**: Task 2
- **Critério de conclusão**: `StreamingResponse` com os headers da RN7; `obter_agente` com cache e
  `RegistroJSONL` (RN6); 422 sem chamar o agente (RN4)
- **Status**: ✅ Concluída

### Task 4: Documentação, verificação manual e sync

- **Cenários BDD**: — (CA9 manual)
- **Tipo**: docs
- **Dependência**: Tasks 1–3
- **Critério de conclusão**: docstring de `src/api/main.py` atualizada; spec 01 cita o endpoint;
  roadmap marca o item; `curl -N` com Ollama e Postgres reais mostrando os passos chegando aos
  poucos e o `/health` respondendo durante a pergunta; ruff e pytest verdes
- **Status**: ✅ Concluída

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4
```

## Progresso

- Total: 4 tasks
- Concluídas: 4/4
- Cenários BDD cobertos: 13/13 (H1–H5, E1–E5, X1–X3; outlines contam como 1)

| Cenário | Teste |
|---|---|
| H1, H3 | `tests/test_api.py::test_h1_h3_pergunta_respondida_vira_stream_de_passos_e_resposta` |
| H2 | `tests/test_api_eventos.py::test_h2_passo_chega_antes_de_o_agente_terminar` |
| H4 | `tests/test_agente_registro.py::test_h4_agente_avisa_cada_passo_depois_de_registrar` |
| H5 | `tests/test_api.py::test_h5_agente_da_api_grava_o_jsonl` |
| E1 | `tests/test_api.py::test_e1_recusas_e_falhas_terminam_com_resposta_nao_respondida` (5 casos) |
| E2 | `tests/test_api_eventos.py::test_e2_acentos_intactos_e_data_numa_linha` |
| E3 | testes das STORY-001 a 003 (`tests/test_agente*.py`), inalterados e verdes |
| E4 | `tests/test_api.py::test_e4_uma_unica_instancia_do_agente` |
| E5 | `tests/test_api_eventos.py::test_e5_agente_roda_fora_da_thread_que_consome` |
| X1 | `tests/test_api.py::test_x1_corpo_invalido_e_barrado_antes_do_agente` (3 casos) e `test_x1_json_malformado_e_barrado` |
| X2 | `tests/test_api_eventos.py::test_x2_excecao_depois_de_um_passo_vira_erro_generico` |
| X3 | `tests/test_api_eventos.py::test_x3_excecao_antes_de_qualquer_passo` e `tests/test_api.py::test_x2_x3_excecao_inesperada_vira_evento_erro` |

## Notas do Sync

- **`anotar` em vez de `_anotar`:** a análise previa um método. Virou uma função interna de
  `responder`, porque depende de `id_pergunta`, `pergunta` e `passos`, que são locais da chamada.
  Um método exigiria passar os três. A spec (RN9) não muda.
- **Gerador testado 20× seguidas** sem falha intermitente (threads sincronizadas por
  `threading.Event`, sem `sleep`).
- **Verificação manual (2026-10-30), Ollama `qwen2.5:7b` em CPU + Postgres reais,**
  `curl -N` em "Quanto foi gasto por UF em 2025?":
  - passo `consultar_sql` em +193 s, passo `gerar_grafico` em +358 s, `resposta` em +359 s:
    os passos chegam aos poucos (CA2);
  - `/health` respondeu em 8 ms com a pergunta em andamento (CA9);
  - o JSONL gravou os dois passos (CA7).
- **Windows:** use `127.0.0.1`, não `localhost`. O `curl` tenta o `::1` primeiro, onde o uvicorn
  não escuta, e a recusa demora cerca de 2 s. O exemplo do README já usa `127.0.0.1`.
- Blueprint confere com o fluxo implementado; sem alteração.

## Pendências (não bloqueantes, de outras stories)

- [ ] "Gastos por UF" virou `tabela`: 28 linhas > `GRAFICO_MAX_BARRAS` (20). É a comparação mais
      comum da demo; avaliar subir o limite para cobrir as UFs (regra da STORY-003).
