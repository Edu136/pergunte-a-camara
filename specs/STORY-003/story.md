# Story: STORY-003 — Gráfico adequado ao formato dos dados

## Descrição

Como **cidadão curioso**,
Quero **ver o resultado da minha pergunta num gráfico apropriado (evolução no tempo, comparação
entre categorias ou só a tabela)**,
Para que **eu entenda os números de relance, sem precisar ler uma tabela**.

## Contexto

Item do bloco 2 do [roadmap](../ROADMAP.md). O contrato `Grafico` (tipo, eixo_x, eixo_y, titulo)
já existe em `src/schemas.py`, mas nada o preenche. Esta story decide o gráfico a partir dos
`dados` da `Resposta` e gera a figura Plotly que a demo vai exibir. A API e a demo são stories
separadas.

Princípios em jogo: P1 (neutralidade — títulos sem adjetivos), P2 (o gráfico só mostra dados
retornados pelo banco).

## Critérios de Aceite

- [ ] **CA1 — Evolução no tempo vira linha:** dados com uma coluna de tempo (`mes`, `ano` ou data)
      e uma coluna numérica geram `tipo = "linha"`, com o tempo no eixo x.
- [ ] **CA2 — Comparação vira barra:** dados com uma coluna de texto (ex.: `uf`, `categoria`) e uma
      coluna numérica geram `tipo = "barra"`, com a categoria no eixo x.
- [ ] **CA3 — Valor único não vira gráfico:** uma linha com um único número (ex.: `SUM`) não gera
      gráfico (`grafico = None`); o número já está nos dados e na explicação.
- [ ] **CA4 — Fora do padrão vira tabela:** formatos não reconhecidos (sem coluna numérica,
      várias colunas de texto, muitas categorias) geram `tipo = "tabela"`.
- [ ] **CA5 — Eixos válidos:** `eixo_x` e `eixo_y` sempre são colunas presentes nos dados; `eixo_y`
      é numérica.
- [ ] **CA6 — Título neutro:** o título descreve só a medida e a dimensão, sem adjetivos (P1).
- [ ] **CA7 — Sem dados, sem gráfico:** respostas com `respondida = false` ou sem linhas não têm gráfico.
- [ ] **CA8 — Figura pronta para a demo:** uma função monta a figura Plotly a partir de `Grafico` e
      `dados`, com valores em reais (R$) e testável sem interface.

## Estimativa

- **Tamanho**: M
- **Complexidade**: Média

## Dependências

| Tipo | Descrição | Status |
|------|-----------|--------|
| Story | STORY-001 (Resposta com dados) | Concluída |
| Biblioteca | Plotly (`requirements.txt`) | Disponível |

## Notas

- `pizza` existe no contrato. Se e quando escolhê-la é decisão da análise.
