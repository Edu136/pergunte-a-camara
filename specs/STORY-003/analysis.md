# Análise — STORY-003: Gráfico adequado ao formato dos dados

## 1. Código relevante

| Módulo | Situação | Uso nesta story |
|---|---|---|
| `src/schemas.py` (`Grafico`, `Resposta.grafico`) | Pronto, sem uso | Contrato preenchido por esta story |
| `src/agent/agente.py` | Pronto | Ao montar a `Resposta` com dados, chama a escolha do gráfico |
| `requirements.txt` (plotly) | Pronto | Figura da demo |
| `.github/workflows/ci.yml` | Ajustar | **Não instala plotly** — mesma armadilha do pandas e do psycopg |

## 2. Domínio

- Os `dados` são `list[dict]` já serializados (números `float`/`int`, datas ISO `str`, `None`).
- Colunas que parecem números mas são **dimensões**: `ano`, `mes`, `deputado_id`, `id_documento`.
- Regras implícitas: valores negativos (compensação de bilhete) aparecem no gráfico como vieram;
  a ordem das linhas é a do SQL (o modelo pode ter usado `ORDER BY`), não é reordenada.

## 3. Direção estratégica

### D1 — Quem escolhe o gráfico: regras fixas × ferramenta do LLM

| | **Regras fixas no agente (recomendado)** | Ferramenta `gerar_grafico` chamada pelo LLM |
|---|---|---|
| Latência | Zero | +1 chamada ao LLM por pergunta (≈ 30–90 s no 7B em CPU) |
| Confiabilidade | Determinística, 100% testável | 7B pode escolher eixos inexistentes ou tipo ruim |
| P1 (título neutro) | Garantido por construção | Título livre do modelo pode ter adjetivo |
| Vitrine "agente" | Menor | Maior (mais uma ferramenta) |

**Recomendação:** regras fixas, registradas como um `PassoAgente` `gerar_grafico` (para a demo e o
log mostrarem a etapa, com `descricao` deixando claro que é automática). O contrato continua aberto
para um *override* pelo LLM no futuro, se a avaliação mostrar ganho — com novo ADR.

### D2 — Regras de escolha

1. Classificar colunas: **medida** = numérica que não é dimensão; **tempo** = `ano`, `mes`, `data*`
   ou texto em formato ISO de data; **categoria** = texto ou id.
2. Sem linhas → `None`.
3. 1 linha e só medidas (sem dimensão) → `None` (valor único, CA3).
4. 1 dimensão de tempo + medida, ≥ 2 linhas, um único `ano` se houver `ano` e `mes` → `linha`.
5. 1 dimensão de categoria + medida, até `GRAFICO_MAX_BARRAS` (padrão 20) linhas → `barra`.
6. Qualquer outro caso → `tabela` (eixos = primeira coluna e primeira medida, ou primeira coluna duas vezes se não houver medida — a demo mostra a tabela inteira).
7. Várias medidas → usa a **primeira** na ordem do `SELECT` (reflete a intenção da consulta).

### D3 — Pizza

Nunca escolhida automaticamente: barras comparam valores com mais precisão, e pizza só faz sentido
para partes de um todo, o que as regras não conseguem saber. Continua no contrato para um *override*
futuro.

### D4 — Título e formato

- Título = `"{medida} por {dimensão}"` com rótulos legíveis (`valor_liquido` → "Valor líquido",
  `uf` → "UF", `mes` → "Mês"; demais: `_` → espaço e primeira letra maiúscula). Neutro por construção.
- Valores em **R$** por padrão; colunas com nome de contagem (`quantidade`, `qtd`, `count`, `total_despesas`, `numero*`) sem R$.
- Separadores pt-BR (`1.234,56`).
- A figura segue a skill `dataviz` (paleta, eixos, rótulos) — carregada antes de escrever o código da figura.

### Estrutura

```
src/tools/grafico.py   escolher_grafico(dados) -> Grafico | None   (puro, sem plotly)
                        montar_figura(grafico, dados) -> plotly Figure
src/agent/agente.py     resposta com dados → escolher_grafico + PassoAgente("gerar_grafico")
```

## 4. Riscos e edge cases

| Risco | Mitigação |
|---|---|
| CI sem plotly | Adicionar `plotly` ao `ci.yml` nesta story |
| Coluna numérica com `None` em algumas linhas | Classificar pela primeira linha não nula; plotly ignora nulos |
| `bool` é `int` em Python | Excluir `bool` de medida |
| `total` ambíguo (R$ ou contagem) | Padrão R$; listar nomes de contagem; o modelo costuma nomear `quantidade`/`qtd` |
| `ano` + `mes` com vários anos | `tabela` (linha misturaria anos) |
| Muitas categorias (ex.: 513 deputados) | Acima de `GRAFICO_MAX_BARRAS` → `tabela` |
| Datas em texto | Reconhecer só ISO (`AAAA-MM-DD`) |
