# Spec BDD: STORY-003 — Gráfico adequado ao formato dos dados

> **Story**: [story.md](story.md) · **Análise**: [analysis.md](analysis.md) · **Fluxo**: [blueprint.mermaid](blueprint.mermaid) · **ADR**: [ADR-002](../../docs/adr/ADR-002-grafico-por-regras.md)
> **Status**: Approved (sincronizada após TDD e /review)
> **Autor**: Edu136
> **Revisores**: —

---

## Feature: Escolha automática do gráfico

A partir dos dados da resposta, o agente escolhe linha, barra, tabela ou nenhum gráfico, com eixos
válidos e título neutro, e monta a figura Plotly que a demo exibe.

### Regras de Negócio

1. **RN1** — Dimensões: `ano`, `mes`, colunas que começam com `data`, texto no formato `AAAA-MM-DD` (tempo); colunas `id` ou terminadas em `_id`, e textos (categoria). Medida: número (`int`/`float`, não `bool`) que não é dimensão. O tipo é decidido pelo primeiro valor não nulo da coluna.
2. **RN2** — Sem linhas, ou 1 linha só com medidas → sem gráfico (`None`).
3. **RN3** — 1 dimensão de tempo + medida, ≥ 2 linhas e, se houver `ano` e `mes`, um único ano → `linha`, com x = coluna de tempo (`mes` quando há `ano` e `mes`).
4. **RN4** — 1 dimensão de categoria + medida, até `GRAFICO_MAX_BARRAS` linhas → `barra`, x = categoria.
5. **RN5** — Qualquer outro formato → `tabela`. Na tabela os eixos são informativos: x = primeira coluna; y = primeira medida, ou a primeira coluna se não houver medida.
6. **RN6** — Com várias medidas, y = a primeira na ordem das colunas.
7. **RN7** — Título = `"{rótulo de y} por {rótulo de x}"` (tabela: `"Resultado da consulta"`). Rótulos: `valor_liquido` → "Valor líquido", `valor_documento` → "Valor do documento", `valor_glosa` → "Valor glosado", `uf` → "UF", `mes` → "Mês", `ano` → "Ano"; demais: `_` vira espaço e só a primeira letra maiúscula.
8. **RN8** — Pizza nunca é escolhida.
9. **RN9** — A figura usa R$ e separadores pt-BR no eixo de valores, eixo de valores a partir de zero, meses como `jan`…`dez`, exceto quando a medida tem nome de contagem (`quantidade`, `qtd`, `count`, `numero`, ou começa com `total_` seguido de plural, como `total_despesas`).
10. **RN10** — Toda resposta com dados ganha um `PassoAgente` `gerar_grafico` com `descricao` "Escolha automática do gráfico" e `saida` = tipo escolhido ou "sem gráfico".

---

### Cenários — Happy Path

```gherkin
Scenario: H1 — Evolução mensal vira linha
  Given os dados [{"mes": 1, "total": 10.0}, {"mes": 2, "total": 12.5}]
  When o gráfico é escolhido
  Then tipo = "linha", eixo_x = "mes", eixo_y = "total" e titulo = "Total por Mês"
```

```gherkin
Scenario: H2 — Comparação por UF vira barra
  Given os dados [{"uf": "MG", "valor_liquido": 10.0}, {"uf": "SP", "valor_liquido": 5.0}]
  When o gráfico é escolhido
  Then tipo = "barra", eixo_x = "uf", eixo_y = "valor_liquido" e titulo = "Valor líquido por UF"
```

```gherkin
Scenario: H3 — Agente preenche o gráfico e registra o passo
  Given o modelo consulta gastos por UF e o banco devolve 2 linhas
  When o agente responde
  Then a Resposta tem grafico do tipo "barra"
  And o último passo é gerar_grafico, com sucesso = true, descricao "Escolha automática do gráfico" e saida "barra"
```

```gherkin
Scenario: H4 — Figura de barras
  Given o gráfico de barras de H2
  When a figura é montada
  Then há uma série de barras com x = ["MG", "SP"] e y = [10.0, 5.0]
  And o título é "Valor líquido por UF", o eixo y tem prefixo "R$ " e os separadores são pt-BR
```

```gherkin
Scenario: H5 — Figura de linha
  Given o gráfico de linha de H1
  When a figura é montada
  Then há uma série em linha com x = [1, 2]
```

---

### Cenários — Edge Cases

```gherkin
Scenario: E1 — Valor único não vira gráfico
  Given os dados [{"total": 2646274.41}]
  When o gráfico é escolhido
  Then o resultado é None
```

```gherkin
Scenario: E2 — Sem linhas
  Given os dados []
  Then o resultado é None
```

```gherkin
Scenario: E3 — Data em texto ISO é tempo
  Given os dados [{"data_emissao": "2025-01-02", "valor_liquido": 1.0}, {"data_emissao": "2025-01-03", "valor_liquido": 2.0}]
  Then tipo = "linha" e eixo_x = "data_emissao"
```

```gherkin
Scenario: E4 — Ano e mês
  Given dados com colunas ano, mes e total, todos do ano 2025
  Then tipo = "linha" e eixo_x = "mes"
  Given dados com colunas ano, mes e total, de 2024 e 2025
  Then tipo = "tabela"
```

```gherkin
Scenario: E5 — Categorias demais
  Given GRAFICO_MAX_BARRAS = 3 e 4 linhas com uf e total
  Then tipo = "tabela"
```

```gherkin
Scenario: E6 — Várias medidas usam a primeira
  Given os dados [{"uf": "MG", "total": 10.0, "quantidade": 3}, {"uf": "SP", "total": 5.0, "quantidade": 2}]
  Then tipo = "barra" e eixo_y = "total"
```

```gherkin
Scenario: E7 — Ids e booleanos não são medidas
  Given os dados [{"deputado_id": 1, "total": 5.0}, {"deputado_id": 2, "total": 3.0}]
  Then tipo = "barra" e eixo_x = "deputado_id"
  Given os dados [{"uf": "MG", "ativo": true}, {"uf": "SP", "ativo": false}]
  Then tipo = "tabela"
```

```gherkin
Scenario: E8 — Contagem sem R$
  Given um gráfico de barras com eixo_y = "quantidade"
  When a figura é montada
  Then o eixo y não tem prefixo "R$ "
```

```gherkin
Scenario: E9 — Rótulos de colunas desconhecidas
  Given os dados [{"nome_parlamentar": "A", "soma_gastos": 1.0}, {"nome_parlamentar": "B", "soma_gastos": 2.0}]
  Then titulo = "Soma gastos por Nome parlamentar"
```

```gherkin
Scenario: E10 — Figura de tabela
  Given um gráfico do tipo tabela com dados de 3 colunas
  When a figura é montada
  Then é uma tabela com os 3 cabeçalhos e todas as linhas
```

```gherkin
Scenario: E11 — Eixo de valores começa em zero
  Given um gráfico de linha com valores entre R$ 1,4 mi e R$ 2 mi
  When a figura é montada
  Then o eixo y começa em zero (um eixo cortado exagera variações — P1)
```

```gherkin
Scenario: E12 — Meses por extenso abreviado
  Given um gráfico de linha com eixo_x = "mes"
  When a figura é montada
  Then o eixo x mostra os 12 meses como "jan", "fev", …, "dez"
```

---

### Cenários — Error Cases

```gherkin
Scenario: X1 — Sem nenhuma medida
  Given os dados [{"uf": "MG", "partido": "X"}, {"uf": "SP", "partido": "Y"}]
  Then tipo = "tabela", eixo_x = "uf", eixo_y = "uf" e titulo = "Resultado da consulta"
```

```gherkin
Scenario: X2 — Resposta não respondida não tem gráfico
  Given o modelo responde sem consultar o banco
  When o agente responde
  Then grafico = None e não há passo gerar_grafico
```

```gherkin
Scenario: X3 — Nulos na medida
  Given os dados [{"uf": "MG", "total": null}, {"uf": "SP", "total": 5.0}]
  Then tipo = "barra" e eixo_y = "total"
```

```gherkin
Scenario: X4 — Barras com categoria numérica (ex.: deputado_id)
  Given um gráfico de barras com eixo_x = "deputado_id" e ids 220593 e 74000
  When a figura é montada
  Then o eixo x é de categorias (uma barra por id, sem escala contínua)
```

```gherkin
Scenario: X5 — Ano no eixo x
  Given um gráfico de linha com eixo_x = "ano" (2024 e 2025)
  When a figura é montada
  Then o eixo x mostra anos inteiros, de 1 em 1, sem separador de milhar
```

```gherkin
Scenario: X6 — Tabela com valores formatados
  Given uma tabela com uf, valor_liquido = 6619024.49 e quantidade = 1200
  When a figura é montada
  Then as células exibem "SP", "R$ 6.619.024,49" (espaço sem quebra) e "1.200"
```

---

## Mapping: Cenário → Teste

| Cenário | Arquivo de Teste | Status |
|---------|-----------------|--------|
| H1, H2, E1–E7, E9, X1, X3 | `tests/test_grafico.py` | 🟢 Green |
| H4, H5, E8, E10, E11, E12, X4, X5, X6 | `tests/test_grafico_figura.py` | 🟢 Green |
| H3, X2 | `tests/test_agente.py` | 🟢 Green |

---

## Notas de Especificação

- Interfaces: `escolher_grafico(dados, max_barras) -> Grafico | None` (puro, sem plotly) e `montar_figura(grafico, dados) -> plotly.graph_objects.Figure`, em `src/tools/grafico.py`.
- Configuração nova: `GRAFICO_MAX_BARRAS=20`.
- O CA5 da story vale para linha e barra; na tabela os eixos são informativos (RN5).
