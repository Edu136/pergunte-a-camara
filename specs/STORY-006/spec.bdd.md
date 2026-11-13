# Spec BDD: STORY-006 — Conjunto de avaliação rotulado por categoria

> **Story**: [story.md](story.md) · **Análise**: [analysis.md](analysis.md) · **Fluxo**: [blueprint.mermaid](blueprint.mermaid)
> **Status**: Approved (sincronizada após TDD)
> **Autor**: Edu136
> **Revisores**: —

---

## Feature: Conjunto fixo de perguntas com o comportamento esperado do agente

O arquivo `experiments/conjunto_avaliacao.json` guarda as perguntas da avaliação, cada uma com a
categoria e o que o agente deveria fazer: responder (com SQL de referência) ou recusar. O CI garante
que o arquivo é válido, seguro e não vaza para o prompt nem para a demo. Um comando confere, no banco
carregado, que todo gabarito executa e devolve dados.

### Regras de Negócio

1. **RN1 — Item:** cada item tem:
   - `id`: prefixo da categoria + 2 dígitos (`F01`, `M10`…);
   - `categoria`: `facil`, `media`, `dificil`, `fora_do_escopo`, `opiniao` ou `injection`;
   - `pergunta`: 5–500 caracteres, igual ao limite de `Pergunta` da API;
   - `respondida`: comportamento esperado do agente;
   - `sql`: SQL de referência, ou `null`;
   - `ordem_importa`: padrão `false`;
   - `nota`: texto livre opcional (interpretação adotada, origem do caso).

   Campos desconhecidos são rejeitados.
2. **RN2 — Prefixo do id:**

   | Categoria | Prefixo |
   |---|---|
   | `facil` | `F` |
   | `media` | `M` |
   | `dificil` | `D` |
   | `fora_do_escopo` | `X` |
   | `opiniao` | `O` |
   | `injection` | `I` |

3. **RN3 — Consistência:**
   - `facil`, `media` e `dificil` ⇒ `respondida = true` e `sql` preenchido;
   - `fora_do_escopo`, `opiniao` e `injection` ⇒ `respondida = false`, `sql = null` e
     `ordem_importa = false`;
   - `ordem_importa = true` exige `ORDER BY` no `sql`.
4. **RN4 — Conjunto:** ids únicos. O conjunto do repositório tem **10 itens por categoria** (mínimo
   aceito: 5).
5. **RN5 — Erro de carga:** `carregar_conjunto(caminho)` lança `ConjuntoInvalido` com mensagem
   clara:

   | Situação | Mensagem contém |
   |---|---|
   | Arquivo ausente | `"Arquivo do conjunto não encontrado: {caminho}"` |
   | JSON malformado, arquivo fora de UTF-8 ou raiz que não é lista | `"Conjunto de avaliação com JSON inválido"` |
   | Item inválido (RN1–RN3) | `"Item {id}: "` + motivo (ou `"Item na posição {i}: "` sem id legível) |
   | Id repetido | `"Ids repetidos: {ids}"` |

6. **RN6 — Gabarito seguro:** todo `sql` passa por `validar_sql` sem exceção, já na carga: um
   gabarito recusado pelo guard torna o item inválido (`"Item {id}: "` + motivo do guard). Gabarito sem ranking
   não usa `LIMIT`; o guard acrescenta o limite na execução.
7. **RN7 — Dificuldade pelo SQL:** `classificar_dificuldade(sql)` olha a consulta escrita (antes do
   guard):
   - **difícil:** tem `JOIN`, subconsulta, CTE ou função de janela;
   - **média:** sem os itens acima, tem `GROUP BY` ou `ORDER BY`;
   - **fácil:** nenhum dos anteriores e no máximo 2 condições no `WHERE` (ligadas por `AND`).

   Fora disso, por exemplo 3 condições sem agrupamento, a classificação é `media`. A categoria de
   cada item respondível é igual à classificação do seu `sql`.
8. **RN8 — Sem vazamento:** `normalizar(texto)` gera minúsculas, sem acento, sem pontuação e com
   espaços colapsados. Há vazamento quando a pergunta normalizada aparece, como sequência de
   palavras inteiras, dentro de algum texto de referência normalizado (igualdade é o caso
   particular). Referências: as perguntas de exemplo e o `PROMPT_SISTEMA`. As perguntas de exemplo são
   `PERGUNTAS_EXEMPLO` da demo, lidas por `ast`, sem executar a página. O teste do conjunto e o
   few-shot do bloco 4 usam a mesma função `vazamentos(perguntas, referencias)`.
9. **RN9 — Neutralidade (P1):** nenhuma pergunta cita deputado pelo nome. Perguntas de `opiniao`
   pedem juízo ("desperdiça", "abusa", "merece"). Ranking só por valor é `media` ou `dificil`, nunca
   `opiniao`.
10. **RN10 — Validação do gabarito no banco** (`python -m src.eval.validar_gabarito [--conjunto
    caminho]`), para cada item respondível, em ordem de id:
    1. `validar_categorias(sql, categorias_do_banco)`;
    2. `ConsultorSQL.consultar(sql)`, que usa `agente_leitura`, `READ ONLY` e `SQL_TIMEOUT_MS`;
    3. o item passa se houver pelo menos 1 linha com algum valor não nulo.

    Saída, uma linha por item:
    - `OK    {id} ({ms} ms)`;
    - `FALHA {id}: {motivo}`. O motivo é a mensagem de `CategoriaInexistente`, `SQLInvalido` ou
      `ErroExecucaoSQL`, ou `"sem dados"`.

    Fecha com o resumo `"Gabarito: {ok} ok, {falhas} falhas de {total}."`.

    Saída do processo:
    - `0` sem falhas;
    - `1` com falhas;
    - `2` se o banco estiver indisponível. Nesse caso a mensagem é
      `"Banco indisponível: suba o Postgres e carregue os dados antes de validar o gabarito."` e
      nenhum item é executado. Erro de SQL ao listar as categorias (ex.: tabela ausente) também
      sai com `2`, com `"Não foi possível listar as categorias: {erro}"`;
    - conjunto inválido: a mensagem de `ConjuntoInvalido` e saída `1`, sem traceback.
11. **RN11 — Só leitura (FF-004):** `src/eval/` entra na lista de pastas que não podem referenciar
    `DATABASE_URL` de escrita.
12. **RN12 — Casos conhecidos:** o conjunto inclui, com `nota` citando a STORY-005:
    - o ranking de categorias (`ordem_importa = true`, `LIMIT` ≥ 5);
    - a soma por categoria em 2025.

---

### Cenários — Happy Path

```gherkin
Scenario: H1 — Conjunto do repositório é válido e balanceado
  Given o arquivo experiments/conjunto_avaliacao.json
  When carregar_conjunto é chamado
  Then nenhum erro é lançado
  And há 10 itens em cada uma das 6 categorias
  And os ids são únicos e seguem o prefixo da categoria
```

```gherkin
Scenario: H2 — Todo gabarito passa no sql_guard
  Given os itens respondíveis do conjunto do repositório
  When validar_sql é chamado com o sql de cada um
  Then nenhum SQLInvalido é lançado
```

```gherkin
Scenario: H3 — Categoria de dificuldade bate com o SQL
  Given os itens facil, media e dificil do conjunto do repositório
  When classificar_dificuldade é chamado com o sql de cada um
  Then o resultado é igual à categoria do item
```

```gherkin
Scenario: H4 — Nenhuma pergunta vaza para a demo ou para o prompt
  Given as perguntas do conjunto do repositório
  And PERGUNTAS_EXEMPLO lidas de app/streamlit_app.py e o PROMPT_SISTEMA
  When vazamentos é chamado
  Then a lista devolvida é vazia
```

```gherkin
Scenario: H5 — Validação do gabarito sem falhas
  Given um conjunto com 2 itens respondíveis e 1 de opiniao
  And um consultor falso que devolve 1 linha com valor para cada SQL
  When o validador roda
  Then a saída tem "OK    F01" e "OK    M01" com o tempo em ms
  And o item de opiniao não é executado
  And o resumo é "Gabarito: 2 ok, 0 falhas de 2."
  And o código de saída é 0
```

```gherkin
Scenario: H6 — Casos conhecidos da STORY-005 estão no conjunto
  Given o conjunto do repositório
  Then existe item com nota citando STORY-005, ordem_importa true e LIMIT >= 5 sobre categorias
  And existe item com nota citando STORY-005 que agrupa por categoria filtrando ano 2025
  And nenhuma pergunta contém nome de deputado presente no banco de exemplo da nota (revisão manual)
```

---

### Cenários — Edge Cases

```gherkin
Scenario: E1 — Vazamento detectado apesar de acento, caixa e pontuação
  Given a pergunta do conjunto "QUANTO foi gasto por uf em 2025"
  And a referência "Quanto foi gasto por UF em 2025?"
  When vazamentos é chamado
  Then a pergunta aparece na lista devolvida
```

```gherkin
Scenario: E2 — Classificação de dificuldade nas fronteiras
  Then classificar_dificuldade devolve:
    | sql                                                                                   | esperado |
    | SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024                              | facil    |
    | SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024 AND uf = 'MG'                | facil    |
    | SELECT SUM(valor_liquido) FROM despesas WHERE ano = 2024 AND uf = 'MG' AND mes = 1    | media    |
    | SELECT uf, SUM(valor_liquido) FROM despesas GROUP BY uf                               | media    |
    | SELECT fornecedor FROM despesas ORDER BY valor_liquido DESC LIMIT 5                   | media    |
    | SELECT d.nome FROM despesas e JOIN deputados d ON d.id = e.deputado_id                | dificil  |
    | WITH t AS (SELECT 1 AS x) SELECT x FROM t                                             | dificil  |
    | SELECT uf, SUM(valor_liquido) / (SELECT SUM(valor_liquido) FROM despesas) FROM despesas GROUP BY uf | dificil |
    | SELECT uf, RANK() OVER (ORDER BY SUM(valor_liquido)) FROM despesas GROUP BY uf        | dificil  |
```

```gherkin
Scenario: E3 — Consulta que só devolve nulos é falha "sem dados"
  Given um item respondível cujo consultor falso devolve [{"total": null}]
  When o validador roda
  Then a saída tem "FALHA F01: sem dados"
  And o código de saída é 1
```

```gherkin
Scenario: E4 — Consulta sem linhas é falha "sem dados"
  Given um item respondível cujo consultor falso devolve []
  When o validador roda
  Then a saída tem "FALHA F01: sem dados"
```

```gherkin
Scenario: E5 — ordem_importa sem ORDER BY é inválido
  Given um item media com ordem_importa true e sql sem ORDER BY
  When carregar_conjunto é chamado
  Then ConjuntoInvalido é lançado com "Item M01: " e "ORDER BY"
```

---

### Cenários — Error Cases

```gherkin
Scenario: X1 — Arquivo ausente ou JSON malformado
  Given um caminho inexistente
  When carregar_conjunto é chamado
  Then ConjuntoInvalido é lançado com "Arquivo do conjunto não encontrado"
  Given um arquivo com JSON malformado, ou com um objeto na raiz em vez de lista
  When carregar_conjunto é chamado
  Then ConjuntoInvalido é lançado com "Conjunto de avaliação com JSON inválido"
```

```gherkin
Scenario Outline: X2 — Item inválido aponta o id
  Given um conjunto com o item <id> que tem <problema>
  When carregar_conjunto é chamado
  Then ConjuntoInvalido é lançado com "Item <id>: "

  Examples:
    | id  | problema                                         |
    | F01 | pergunta com 3 caracteres                        |
    | F01 | categoria "trivial"                              |
    | F01 | campo desconhecido "esperado"                    |
    | M01 | categoria facil (prefixo não bate)               |
    | F01 | categoria facil sem sql                          |
    | F01 | categoria facil com respondida false             |
    | O01 | categoria opiniao com sql preenchido             |
    | I01 | categoria injection com respondida true          |
    | O01 | categoria opiniao com ordem_importa true         |
    | M01 | sql com erro de sintaxe                          |

  E um item sem id legível aponta a posição: "Item na posição 2: ".
```

```gherkin
Scenario: X3 — Ids repetidos
  Given um conjunto com dois itens de id "F01"
  When carregar_conjunto é chamado
  Then ConjuntoInvalido é lançado com "Ids repetidos: F01"
```

```gherkin
Scenario: X4 — Falhas do gabarito no banco listadas com motivo
  Given 3 itens respondíveis
  And o primeiro filtra uma categoria que não existe no banco
  And o consultor falso lança ErroExecucaoSQL de timeout para o segundo
  And o terceiro devolve dados
  When o validador roda
  Then a saída tem "FALHA F01: Categoria" com a sugestão de validar_categorias
  And "FALHA F02: A consulta excedeu o tempo limite"
  And "OK    F03"
  And o resumo é "Gabarito: 1 ok, 2 falhas de 3."
  And o código de saída é 1
```

```gherkin
Scenario: X5 — Banco indisponível aborta antes dos itens
  Given a listagem de categorias lança BancoIndisponivel
  When o validador roda
  Then a saída é "Banco indisponível: suba o Postgres e carregue os dados antes de validar o gabarito."
  And nenhuma consulta de item é executada
  And o código de saída é 2
```

```gherkin
Scenario: X6 — Código de avaliação só usa a conexão de leitura
  Given os arquivos .py de src/eval
  When a FF-004 roda
  Then nenhum referencia DATABASE_URL de escrita
```

---

## Mapping: Cenário → Teste

| Cenário | Arquivo de Teste | Status |
|---------|-----------------|--------|
| H1, H2, H3, H4, H6 + RN6 (LIMIT só em ranking) | `tests/test_eval_conjunto_repositorio.py` | 🟢 Green |
| H5, E3, E4, X4, X5 | `tests/test_eval_validar_gabarito.py` | 🟢 Green |
| E1, E2, E5, X1, X2, X3 | `tests/test_eval_conjunto.py` | 🟢 Green |
| X6 | `tests/test_arquitetura.py` | 🟢 Green |
| CA5 real (banco carregado) | `python -m src.eval.validar_gabarito`: 30 ok, 0 falhas (ver tasks.md) | 🟢 Green |

---

## Notas de Especificação

- **Fora do CI:** a execução real do gabarito (CA5) depende do banco carregado. O CI cobre o
  validador com consultor falso. A execução real é registrada em `tasks.md` com o resumo.
- **H6, nomes de deputado:** a ausência de nomes é verificada na revisão. Um teste automático
  precisaria do cadastro, que não está no CI.
- **Sem números no gabarito:** o harness (próxima story) compara o resultado do SQL do agente com o
  do SQL de referência, executados no mesmo banco. Nomes de coluna e arredondamento são decisão do
  harness.
- **Partido/UF "da época":** o CSV da CEAP repete o partido e a UF **atuais** em todas as linhas do
  deputado. No banco, `despesas.partido` nunca difere de `deputados.partido`. Por isso o conjunto não
  tem pergunta que dependa dessa diferença (ver a pendência em `tasks.md`).
- **Lideranças** têm `uf = 'NA'` e `partido` nulo. Perguntas por UF ou partido dizem "deputados" e o
  gabarito filtra `deputado_id IS NOT NULL`.
- **Anos sem dados** (ex.: 2019) ficam fora deste conjunto: "não há dados" é resposta correta, não
  recusa. Ver `analysis.md`.
