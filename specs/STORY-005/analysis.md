# Análise — STORY-005: Demo em Streamlit com os passos do agente em tempo real

## 1. Código relevante

| Módulo | Situação | Uso nesta story |
|---|---|---|
| `app/streamlit_app.py` | Placeholder "Em construção" | Vira a página da demo (só desenho) |
| `src/api/main.py` (`POST /perguntar`) | Pronto (STORY-004) | Servidor consumido pela demo via SSE |
| `src/schemas.py` (`PassoAgente`, `Resposta`, `Pergunta`) | Pronto | Valida os eventos recebidos e a pergunta antes do envio (CA1) |
| `src/tools/grafico.py` (`montar_figura`, `rotulo`) | Pronto | Gráfico e tabela pt-BR da resposta |
| `src/config.py` | Sem endereço da API | Recebe `API_URL` e `DEMO_TIMEOUT_S` (CA7) |
| Versões instaladas | Streamlit 1.66, httpx 0.28, Plotly 7.1 | `st.status`, `st.pills` e `streamlit.testing.v1.AppTest` disponíveis |

**Armadilha encontrada:** o projeto não é instalado como pacote. O pytest usa `pythonpath = ["."]`,
mas `streamlit run app/streamlit_app.py` põe só `app/` no `sys.path`, então `import src...` falha.
Hoje passa despercebido porque o placeholder não importa nada de `src`.

## 2. Domínio

- Nenhum conceito novo. A demo é mais um cliente da `Resposta`: lê os mesmos contratos que a API
  publica.
- Regras explícitas:
  - **P1:** os textos fixos da página e as perguntas de exemplo não têm adjetivo de juízo nem nome
    de deputado. Ranking só como "maiores valores".
  - **P2:** quando há dados, SQL e fonte sempre visíveis, mais o aviso fixo "Verifique na fonte
    oficial".
- Regras implícitas:
  - **A explicação vem do LLM e cita valores em reais.** O `st.markdown` interpreta `$…$` como
    LaTeX: "R$ 10,00 e R$ 20,00" viraria fórmula e o número sumiria da tela, ferindo P2. É preciso
    escapar o `$`.
  - **Números na tela em pt-BR.** Lição da STORY-003 (X6): conferir o texto exibido, não a
    configuração.
  - **Resposta não respondida** não tem SQL nem dados. Não mostrar blocos vazios.

## 3. Direção estratégica

### D1 — Onde mora a lógica: cliente na `src/`, página na `app/`

`src/api/cliente.py`, puro e sem Streamlit:

- `ler_sse(linhas) -> Iterator[tuple[str, str]]` transforma o texto SSE em `(evento, data)`.
- `perguntar(texto, config, transporte=None) -> Iterator[Evento]` faz o POST em stream e devolve os
  eventos já validados:
  - `PassoRecebido(passo: PassoAgente)`
  - `RespostaRecebida(resposta: Resposta)`
  - `Falha(mensagem: str)`
- Toda falha de transporte vira `Falha` com mensagem amigável, e o gerador **sempre termina com
  exatamente um** `RespostaRecebida` ou `Falha` (espelho da RN2 da API). Os casos cobertos:
  - API fora (`ConnectError`);
  - timeout;
  - `422` e outros status ≠ 200;
  - evento `erro`;
  - stream que acaba sem evento final;
  - JSON inválido.
- O transporte é injetável: nos testes entra `httpx.MockTransport`, sem servidor (CA8).

`app/streamlit_app.py` só desenha. Para o `import src` funcionar com `streamlit run`, a página
insere a raiz do repositório no `sys.path` (2 linhas). A alternativa seria empacotar o projeto
(`pip install -e .`), mas isso exige `[project]` e build backend no `pyproject` só por causa
disso: over-engineering para 1 script.

### D2 — Desenho dos passos (CA3)

`st.status("Consultando os dados…", expanded=True)` recebe uma linha por passo, assim que o passo
chega. A linha mostra:
- ícone de sucesso ou falha;
- descrição;
- resultado (nº de linhas ou tipo de gráfico) ou erro;
- duração.

O SQL de cada consulta aparece em `st.code` na própria linha, porque o `st.status` é um expander e
o Streamlit **não permite expander dentro de expander**. No fim, o status vira "Concluído"
(`complete`) ou "Não foi possível concluir" (`error`). O `st.status` já mostra animação de
andamento enquanto está em `running`, então o indicador de andamento sai de graça.

### D3 — Desenho da resposta (CA4, CA5)

| Situação | O que aparece |
|---|---|
| `respondida = true`, gráfico `linha`/`barra` | Explicação → gráfico → tabela de dados → SQL → fontes → aviso |
| `respondida = true`, gráfico `tabela` | Explicação → tabela → SQL → fontes → aviso (sem tabela duplicada) |
| `respondida = true`, sem gráfico (valor único) | Explicação → tabela (1 linha) → SQL → fontes → aviso |
| `respondida = false` | `st.warning(explicacao)`. Mais nada |

**Tabela de dados:** sempre a tabela pt-BR de `montar_figura` (tipo `tabela`), que já formata R$ e
separadores (X6 da STORY-003). O `st.dataframe` mostraria `6619024.49`.

**Explicação:** `st.markdown` com `$` escapado (`\$`). O HTML já vem desligado por padrão
(`unsafe_allow_html=False`).

**Fontes:** links em markdown.

**Aviso:** constante `AVISO_FONTE`.

### D4 — Estado entre interações (CA9) e perguntas de exemplo (CA2)

- A pergunta só roda no envio (botão do formulário ou clique num exemplo).
- Durante a execução, passos e resultado vão para `st.session_state["ultima"]`. Nas reexecuções
  sem envio, a página redesenha a partir do estado, sem chamar a API.
- Os exemplos ficam em `st.pills`. O clique dispara um callback que grava a pergunta e marca o
  envio. A lista vem de uma constante `PERGUNTAS_EXEMPLO`, testada contra P1 (sem nomes, sem
  adjetivos de juízo).

### D5 — Config (CA7)

| Variável | Padrão | Motivo |
|---|---|---|
| `API_URL` | `http://127.0.0.1:8000` | Usa `127.0.0.1` em vez de `localhost` (a lição do IPv6 no Windows, STORY-004) |
| `DEMO_TIMEOUT_S` | `900` | É o tempo máximo **entre eventos** (o `read` do httpx), não o total. O pior caso de um passo é `OLLAMA_TIMEOUT_S` (300); 900 cobre com folga |

O timeout de conexão é curto e fixo (5 s): a API fora do ar aparece logo.

### D6 — API e demo sobem separadas

São dois comandos (`uvicorn …` e `streamlit run …`), como o README já documenta. Subir a API de
dentro da demo misturaria responsabilidades. Se a API estiver fora, o CA6 dá uma mensagem clara
("A API não está respondendo em {API_URL}…").

### D7 — Testes

- **Cliente (`tests/test_api_cliente.py`):** parser, eventos válidos, cada tipo de falha e garantia
  de evento final, tudo com `httpx.MockTransport`.
- **Página (`tests/test_demo.py`):** `AppTest.from_file` com `perguntar` substituído por um falso
  (via `unittest.mock.patch`). Cobre validação local, exemplos, os três desenhos da resposta,
  falha com passos preservados, reexecução sem nova chamada e `$` escapado.
- **Tempo real ponta a ponta:** verificação manual com API, Ollama e Postgres reais. O `AppTest`
  roda o script até o fim e não observa a atualização incremental.

### Estrutura

```
src/config.py           + api_url, demo_timeout_s
src/api/cliente.py      ler_sse, perguntar, PassoRecebido / RespostaRecebida / Falha
app/streamlit_app.py    sys.path, formulário + exemplos, st.status dos passos, resposta, estado
tests/test_api_cliente.py, tests/test_demo.py
```

## 4. Riscos e edge cases

| Risco | Mitigação |
|---|---|
| `import src` falha com `streamlit run` | `sys.path` na página; verificação manual com o comando do README |
| `$` da explicação vira LaTeX e some com o valor | Escapar `$` e testar o texto exibido |
| Expander dentro do `st.status` gera erro do Streamlit | SQL em `st.code` direto na linha do passo, sem expander |
| Clique duplo / reenvio enquanto a pergunta roda | O Streamlit executa um script por vez por sessão; o botão do formulário fica bloqueado durante a execução. Aceito |
| Stream interrompido no meio (API reiniciada) | `httpx.RemoteProtocolError`/`ReadError` viram `Falha`; os passos já desenhados ficam (CA6) |
| Evento com JSON inválido ou schema diferente (versões de API e demo desalinhadas) | `ValidationError` vira `Falha` genérica e o detalhe vai para o log |
| `AppTest` e `mock.patch`: a página precisa buscar `perguntar` no módulo na hora da chamada | A página usa `cliente.perguntar(...)` (atributo do módulo), não `from … import perguntar` |
| Tabela com 200 linhas pesa no `go.Table` | Aceito (limite já é `SQL_LIMITE_LINHAS`) |
| CI sem `streamlit` (o `ci.yml` instala uma lista explícita) | Adicionar `streamlit` ao CI nesta story (mesma armadilha do plotly) |
