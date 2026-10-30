# Tasks: STORY-005 — Demo em Streamlit com os passos do agente em tempo real

> **Story**: [story.md](story.md)
> **Spec**: [spec.bdd.md](spec.bdd.md)

## Tasks

### Task 1: Configuração e CI

- **Cenários BDD**: base (E7)
- **Tipo**: setup
- **Dependência**: —
- **Critério de conclusão**: `API_URL` e `DEMO_TIMEOUT_S` em `Settings` e `.env.example`;
  `streamlit` instalado no CI
- **Status**: ⏳ Pendente

### Task 2: Cliente SSE da API

- **Cenários BDD**: H1, H2, E1, E7, X1
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: `src/api/cliente.py` com `ler_sse`, `perguntar` e os eventos
  `PassoRecebido` / `RespostaRecebida` / `Falha`; sem importar Streamlit (RN3, RN4, RN5)
- **Status**: ⏳ Pendente

### Task 3: Página — pergunta, exemplos e passos

- **Cenários BDD**: H5, H6, E6, X2
- **Tipo**: feature
- **Dependência**: Task 2
- **Critério de conclusão**: `sys.path` para `import src`; formulário com validação local (RN1);
  `PERGUNTAS_EXEMPLO` (RN2); `st.status` com as linhas dos passos (RN6, RN7); testes com `AppTest`
- **Status**: ⏳ Pendente

### Task 4: Página — resposta, falhas e estado

- **Cenários BDD**: H3, H4, E2, E3, E4, E5, X3
- **Tipo**: feature
- **Dependência**: Task 3
- **Critério de conclusão**: desenho da resposta (RN8, RN9, RN10) e estado em `session_state`
  (RN11); testes com `AppTest`
- **Status**: ⏳ Pendente

### Task 5: Documentação, verificação manual e sync

- **Cenários BDD**: — (tempo real da CA3, manual)
- **Tipo**: docs
- **Dependência**: Tasks 1–4
- **Critério de conclusão**:
  - docstring da página atualizada; README com os dois comandos e o `.env`;
  - roadmap marca o item;
  - API, Ollama e Postgres reais com `streamlit run`, conferindo:
    - os passos aparecendo um a um;
    - os números em pt-BR na tela;
  - ruff e pytest verdes
- **Status**: ⏳ Pendente

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5
```

## Progresso

- Total: 5 tasks
- Concluídas: 0/5
- Cenários BDD cobertos: 0/16 (H1–H6, E1–E7, X1–X3; outlines contam como 1)
