# Spec BDD: STORY-002 — Validar categorias citadas no SQL e sinalizar resultado vazio

> **Story**: [story.md](story.md) · **Fluxo base**: [STORY-001/blueprint.mermaid](../STORY-001/blueprint.mermaid)
> **Status**: Approved (sincronizada após TDD)
> **Autor**: Edu136
> **Revisores**: —

---

## Feature: Validação de categorias e resultado vazio

Antes de executar, o agente confere se os textos de categoria citados no SQL existem de fato; se
não, devolve ao modelo sugestões das categorias oficiais. Resultados vazios ou nulos chegam ao
modelo com aviso explícito para que ele não invente valores.

### Regras de Negócio

1. **RN1** — São validadas comparações entre a coluna `categoria` (com ou sem prefixo de tabela) e textos literais, via `=`, `<>`, `!=` e `IN`, em qualquer lado da comparação.
2. **RN2** — A comparação é exata (como no Postgres); a busca de sugestões ignora maiúsculas e devolve no máximo 3 categorias: primeiro as que **contêm** o texto, depois as mais parecidas.
3. **RN3** — Categoria inexistente lança `CategoriaInexistente` (subclasse de `SQLInvalido`): a consulta não vai ao banco e conta como falha corrigível.
4. **RN4** — Sem lista de categorias carregada, a validação é ignorada.
5. **RN5** — `LIKE`/`ILIKE` e comparações com outras colunas não são validados.
6. **RN6** — Resultado sem linhas, ou com todos os valores nulos, é devolvido ao modelo com o aviso "Nenhum registro encontrado: não informe valores".

---

### Cenários — Happy Path

```gherkin
Scenario: H1 — Categoria exata executa
  Given as categorias "COMBUSTÍVEIS E LUBRIFICANTES." e "TELEFONIA"
  When o SQL "SELECT SUM(valor_liquido) FROM despesas WHERE categoria = 'COMBUSTÍVEIS E LUBRIFICANTES.'" é validado
  Then nenhum erro é lançado
```

```gherkin
Scenario: H2 — Agente corrige a categoria a partir da sugestão
  Given o modelo pede uma consulta com categoria = 'COMBUSTÍVEIS E LUBRIFICANTES'
  And depois pede a mesma consulta com 'COMBUSTÍVEIS E LUBRIFICANTES.'
  When o agente responde
  Then a 1ª consulta não foi executada no banco
  And o modelo recebeu um erro sugerindo 'COMBUSTÍVEIS E LUBRIFICANTES.'
  And a Resposta tem respondida = true com o SQL corrigido
```

---

### Cenários — Edge Cases

```gherkin
Scenario: E1 — IN, diferente e coluna com prefixo
  Given as categorias "TELEFONIA" e "SERVIÇOS POSTAIS"
  When são validados "... WHERE d.categoria IN ('TELEFONIA', 'CORREIOS')", "... WHERE categoria <> 'TELEFONE'" e "... WHERE 'TELEFONE' = categoria"
  Then todos lançam CategoriaInexistente citando o texto inválido
```

```gherkin
Scenario: E2 — Diferença só de maiúsculas
  Given a categoria "TELEFONIA"
  When o SQL compara categoria = 'telefonia'
  Then lança CategoriaInexistente sugerindo "TELEFONIA"
```

```gherkin
Scenario: E3 — Sem lista de categorias
  Given a lista de categorias vazia
  When um SQL com categoria = 'QUALQUER' é validado
  Then nenhum erro é lançado
```

```gherkin
Scenario: E4 — LIKE e comparação entre colunas não são validados
  Given a categoria "TELEFONIA"
  When são validados "... WHERE categoria ILIKE 'telef%'" e "... WHERE categoria = subcategoria"
  Then nenhum erro é lançado
```

```gherkin
Scenario: E5 — Resultado nulo ou vazio é sinalizado ao modelo
  Given os resultados [] e [{"total": null}]
  When são formatados para o modelo
  Then ambos contêm "Nenhum registro encontrado: não informe valores"
  And [{"total": 0}] não contém o aviso
```

```gherkin
Scenario: E6 — Texto contido numa categoria vira sugestão
  Given a categoria "COMBUSTÍVEIS E LUBRIFICANTES."
  When o SQL compara categoria = 'combustíveis'
  Then lança CategoriaInexistente sugerindo "COMBUSTÍVEIS E LUBRIFICANTES."
```

---

### Cenários — Error Cases

```gherkin
Scenario: X1 — Sem nada parecido
  Given a categoria "TELEFONIA"
  When o SQL compara categoria = 'XYZ'
  Then lança CategoriaInexistente informando que deve ser usada uma das categorias listadas no prompt
```

```gherkin
Scenario: X2 — Categoria errada conta para o limite de correções
  Given AGENTE_MAX_CORRECOES = 1 e o modelo sempre usa uma categoria inexistente
  When o agente responde
  Then nenhuma consulta é executada no banco
  And a Resposta tem respondida = false
```

---

## Mapping: Cenário → Teste

| Cenário | Arquivo de Teste | Status |
|---------|-----------------|--------|
| H1, E1, E2, E3, E4, E6, X1 | `tests/test_validar_categorias.py` | 🟢 Green |
| H2, X2 | `tests/test_agente.py` | 🟢 Green |
| E5 | `tests/test_agente_prompts.py` | 🟢 Green |

---

## Notas de Especificação

- Interface: `validar_categorias(sql: str, categorias: list[str]) -> None` em `src/tools/validar_categorias.py`.
- O sql recebido já passou pelo `sql_guard` no consultor? **Não**: a validação roda no agente antes de `consultar`. Se o SQL não compilar, a validação não faz nada e o guard rejeita em seguida.
