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
- **Status**: ✅ Concluída

### Task 2: Cliente SSE da API

- **Cenários BDD**: H1, H2, E1, E7, X1
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: `src/api/cliente.py` com `ler_sse`, `perguntar` e os eventos
  `PassoRecebido` / `RespostaRecebida` / `Falha`; sem importar Streamlit (RN3, RN4, RN5)
- **Status**: ✅ Concluída

### Task 3: Página — pergunta, exemplos e passos

- **Cenários BDD**: H5, H6, E6, X2
- **Tipo**: feature
- **Dependência**: Task 2
- **Critério de conclusão**: `sys.path` para `import src`; formulário com validação local (RN1);
  `PERGUNTAS_EXEMPLO` (RN2); `st.status` com as linhas dos passos (RN6, RN7); testes com `AppTest`
- **Status**: ✅ Concluída

### Task 4: Página — resposta, falhas e estado

- **Cenários BDD**: H3, H4, E2, E3, E4, E5, X3
- **Tipo**: feature
- **Dependência**: Task 3
- **Critério de conclusão**: desenho da resposta (RN8, RN9, RN10) e estado em `session_state`
  (RN11); testes com `AppTest`
- **Status**: ✅ Concluída

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
- **Status**: ✅ Concluída

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5
```

## Progresso

- Total: 5 tasks
- Concluídas: 5/5
- Cenários BDD cobertos: 16/16 (H1–H6, E1–E7, X1–X3; outlines contam como 1)

| Cenário | Teste |
|---|---|
| H1 | `tests/test_api_cliente.py::test_h1_stream_vira_eventos_validados` |
| H2 | `tests/test_api_cliente.py::test_h2_leitor_de_sse_separa_eventos_e_ignora_comentarios` |
| H3 | `tests/test_demo.py::test_h3_resposta_com_grafico_de_barras` |
| H4 | `tests/test_demo.py::test_h4_grafico_tabela_nao_duplica_a_tabela` |
| H5 | `tests/test_demo.py::test_h5_pergunta_de_exemplo_e_enviada_ao_clicar` |
| H6 | `tests/test_demo.py::test_h6_passos_com_resultado_duracao_e_sql` |
| E1 | `tests/test_api_cliente.py::test_e1_cada_evento_chega_assim_que_e_lido` |
| E2 | `tests/test_demo.py::test_e2_valor_unico_mostra_so_a_tabela` |
| E3 | `tests/test_demo.py::test_e3_resposta_nao_respondida_vira_so_aviso` |
| E4 | `tests/test_demo.py::test_e4_valores_em_reais_nao_viram_formula` |
| E5 | `tests/test_demo.py::test_e5_interagir_com_a_pagina_nao_refaz_a_pergunta` |
| E6 | `tests/test_demo.py::test_e6_perguntas_de_exemplo_neutras_e_validas` |
| E7 | `tests/test_api_cliente.py::test_e7_endereco_e_timeouts_vem_da_config` |
| X1 | `tests/test_api_cliente.py::test_x1_falhas_viram_uma_unica_falha_amigavel` (8 casos) e `test_x1_mensagem_de_api_fora_cita_o_endereco` |
| X2 | `tests/test_demo.py::test_x2_pergunta_invalida_e_barrada_na_pagina` |
| X3 | `tests/test_demo.py::test_x3_falha_depois_de_um_passo_preserva_o_passo` |

## Notas do Sync

- **Exemplos lidos pelo `AppTest`:** o teste chegou a executar a página fora do Streamlit para ler
  `PERGUNTAS_EXEMPLO`. O `with st.form` ficava preso no contexto global e os `AppTest` seguintes
  acusavam "callback dentro de form" no `st.pills`. Agora as opções são lidas das pills
  renderizadas. A fixture também falha se a página levantar exceção, porque o `AppTest` só guarda
  o erro e não o propaga.
- **`import src` conferido** rodando a página de outra pasta: só o `sys.path` da página resolve.
- **README:** o exemplo com `curl` da STORY-004 tinha perdido o `\` de continuação de linha;
  corrigido.
- Blueprint confere com o fluxo implementado; sem alteração.
- **Verificação ponta a ponta (2026-10-30)**: `AppTest` com o cliente **real**, contra API,
  Ollama `qwen2.5:7b` em CPU e Postgres reais:
  - **1ª tentativa (modelo frio):** a 1ª chamada ao Ollama passou de `OLLAMA_TIMEOUT_S` (300 s).
    A página mostrou "O modelo de linguagem está indisponível…" como aviso neutro, sem exceção (E3).
  - **2ª tentativa (modelo quente), "Quais categorias tiveram os maiores valores em 2025?", 300 s:**
    - duas consultas ❌ por timeout de 5 s e a terceira ✅, ou seja, a autocorreção apareceu
      passo a passo;
    - gráfico de barras e tabela com `R$ 102.059.920,94` (pt-BR);
    - explicação com `R\$` escapado, SQL, fonte e aviso de fonte oficial.
  - O tempo real visual (passos surgindo um a um no navegador) fica para a conferência do autor.

## Pendências (não bloqueantes, de outras stories)

- [ ] **Modelo frio estoura `OLLAMA_TIMEOUT_S` (300 s)** na 1ª pergunta depois de o modelo sair
      da memória. Avaliar aquecer o modelo ao subir a API ou subir o timeout.
- [ ] **`GROUP BY categoria` em 2025 estourou o `statement_timeout` de 5 s duas vezes** (banco
      recém-iniciado, cache frio). Avaliar índice por `ano`/`categoria`.
- [ ] **"Quais categorias… maiores valores" virou `LIMIT 1`** (uma barra só). Orientar o modelo a
      trazer um ranking (prompt/few-shot, bloco 4). Avaliar também se 1 linha com categoria deve
      virar gráfico (regra da STORY-003).
