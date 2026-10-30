# Story: STORY-005 — Demo em Streamlit com os passos do agente em tempo real

## Descrição

Como **cidadão curioso ou jornalista de dados**,
Quero **fazer uma pergunta numa página web e ver o agente trabalhando passo a passo, até a resposta
com explicação, gráfico, SQL e fonte**,
Para que **eu entenda os gastos da cota sem planilha nem SQL e consiga conferir de onde veio cada
número**.

## Contexto

Último item do bloco 2 do [roadmap](../ROADMAP.md). A API `POST /perguntar` (STORY-004) já entrega
os passos por SSE e a `Resposta` completa. A figura Plotly já sai de `montar_figura` (STORY-003).
Hoje `app/streamlit_app.py` só mostra "Em construção". Esta story transforma a página num cliente da
API. A demo **não importa o agente**: tudo passa pelo HTTP, como passaria para qualquer outro
cliente.

Princípios em jogo:
- **P1 (neutralidade):** textos da página e perguntas de exemplo sem juízo e sem nome de deputado.
- **P2 (fidelidade):** SQL e fonte sempre visíveis quando há dados, mais o aviso "verifique na
  fonte oficial".

## Critérios de Aceite

- [ ] **CA1 — Pergunta:** a página tem um campo de pergunta e um botão de enviar. Se o texto estiver
      fora de 5–500 caracteres, a página avisa na hora, sem chamar a API.
- [ ] **CA2 — Perguntas de exemplo:** a página oferece algumas perguntas prontas, neutras e sem nome
      de deputado. Clicar numa delas envia essa pergunta.
- [ ] **CA3 — Passos em tempo real:** cada evento `passo` aparece assim que chega, com a descrição,
      o resultado (nº de linhas ou tipo de gráfico) ou o erro, e a duração. O SQL de cada consulta
      fica disponível para quem quiser ver. Enquanto a pergunta roda, há um indicador de andamento.
- [ ] **CA4 — Resposta respondida:** a página mostra:
  - a explicação;
  - o gráfico (`montar_figura`), quando houver;
  - os dados em tabela;
  - o SQL executado;
  - as fontes como links;
  - o aviso fixo "Verifique na fonte oficial".
- [ ] **CA5 — Resposta não respondida:** com `respondida = false`, a página mostra a explicação do
      agente como aviso neutro, sem gráfico, SQL nem tabela vazia.
- [ ] **CA6 — Falhas:** evento `erro`, API fora do ar, `422` ou stream interrompido viram uma
      mensagem amigável, sem detalhes técnicos. Os passos já recebidos continuam visíveis.
- [ ] **CA7 — Espera longa não estoura:** a pergunta leva minutos no modelo local em CPU, então a
      demo não desiste por timeout curto. O endereço da API e o tempo máximo de espera vêm da
      config (`.env`).
- [ ] **CA8 — Lógica testável sem interface:** a leitura do SSE e o cliente da API ficam fora do
      Streamlit, em funções testadas com pytest. A página só desenha.
- [ ] **CA9 — Última resposta preservada:** interagir com a página (abrir o SQL, expandir um passo)
      não apaga a última resposta nem refaz a pergunta.

## Estimativa

- **Tamanho**: M
- **Complexidade**: Média

## Dependências

| Tipo | Descrição | Status |
|------|-----------|--------|
| Story | STORY-004 (API com SSE) | Concluída |
| Story | STORY-003 (`montar_figura`) | Concluída |
| Biblioteca | Streamlit, Plotly e httpx (`requirements.txt`) | Disponível |

## Notas

- Fica para a análise:
  - onde mora o cliente SSE (`src/api/cliente.py`? `app/`?);
  - como desenhar os passos (`st.status`, expander, lista);
  - como testar a página (`streamlit.testing.AppTest` ou só as funções);
  - se a API sobe junto (dois processos) ou fica a cargo de quem roda.
- Fora do escopo:
  - conversa com perguntas de acompanhamento (bloco 7);
  - mapa por UF (bloco 6);
  - GIF e vídeo da demo (bloco 9);
  - link da nota fiscal por linha (`url_documento`): o SQL precisaria selecioná-lo, assunto de
    prompt/few-shot;
  - autenticação.
