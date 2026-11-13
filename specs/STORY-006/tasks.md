# Tasks: STORY-006 — Conjunto de avaliação rotulado por categoria

> **Story**: [story.md](story.md)
> **Spec**: [spec.bdd.md](spec.bdd.md)

## Tasks

### Task 1: Schema e carga do conjunto

- **Cenários BDD**: E5, X1, X2, X3
- **Tipo**: feature
- **Dependência**: —
- **Critério de conclusão**: `src/eval/conjunto.py` com `ItemAvaliacao`, `carregar_conjunto` e
  `ConjuntoInvalido` (RN1–RN5); testes em `tests/test_eval_conjunto.py` verdes
- **Status**: ✅ Concluída

### Task 2: Classificação de dificuldade e vazamento

- **Cenários BDD**: E1, E2
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: `classificar_dificuldade`, `normalizar`, `vazamentos` e a leitura de
  `PERGUNTAS_EXEMPLO` por `ast` (RN7, RN8)
- **Status**: ✅ Concluída

### Task 3: Validador do gabarito no banco

- **Cenários BDD**: H5, E3, E4, X4, X5, X6
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: `python -m src.eval.validar_gabarito` com consultor e categorias
  injetáveis, saída e códigos de saída da RN10; `src/eval` na FF-004
- **Status**: ✅ Concluída

### Task 4: Conjunto de 60 perguntas

- **Cenários BDD**: H1, H2, H3, H4, H6
- **Tipo**: feature (dados)
- **Dependência**: Tasks 1 e 2
- **Critério de conclusão**: `experiments/conjunto_avaliacao.json` com 10 itens por categoria;
  regra de dificuldade e categorias de injection documentadas em `experiments/README.md`;
  `tests/test_eval_conjunto_repositorio.py` verde
- **Status**: ✅ Concluída

### Task 5: Execução real do gabarito (CA5)

- **Cenários BDD**: CA5 (manual)
- **Tipo**: test
- **Dependência**: Tasks 3 e 4
- **Critério de conclusão**: `python -m src.eval.validar_gabarito` com o banco carregado termina
  com 0 falhas; resumo registrado abaixo
- **Status**: ✅ Concluída

### Task 6: Sync e documentação

- **Cenários BDD**: todos
- **Tipo**: docs
- **Dependência**: Task 5
- **Critério de conclusão**: mapping da spec atualizado, ROADMAP marcado, README e DOMAIN apontando
  para o conjunto
- **Status**: ✅ Concluída

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6
```

## Progresso

- Total: 6 tasks
- Concluídas: 6/6
- Cenários BDD cobertos: 17/17

## Dados de referência (banco local, 2026-11-13)

- 441.999 despesas, 2024–2025, 619 deputados, 28 UFs, 22 partidos, 20 categorias.
- `GROUP BY ano, categoria` em toda a tabela: 0,7 s com cache quente.
- Categorias com total negativo (`COMPLEMENTAÇÃO DO AUXÍLIO-MORADIA`; em 2025 também
  `PASSAGEM AÉREA - MISSÃO OFICIAL`): bons casos para o gabarito não filtrar negativos.

## Execução real do gabarito (Task 5, 2026-11-13)

```
$ python -m src.eval.validar_gabarito
...
Gabarito: 30 ok, 0 falhas de 30.     (exit 0; consulta mais lenta: 1,4 s, D03)
```

A 1ª execução teve `FALHA D08: sem dados`. A pergunta original, "gasto dos deputados cujo partido
atual difere do partido na época da despesa", não tem como dar resultado com estes dados (ver as
pendências). A D08 foi trocada por "percentual do gasto de 2025 que coube às lideranças".

## Divergências registradas no sync

- **RN8:** o vazamento passou a ser "contido por palavras inteiras em qualquer referência", e não
  "igual ao exemplo ou contido no prompt". É mais rígido, e a igualdade continua coberta.
- **X2:** a implementação ganhou 3 variações além das 8 da spec:
  - recusa com `ordem_importa`;
  - SQL com erro de sintaxe;
  - item sem id legível, que aponta a posição.
- **RN6:** ganhou teste próprio no conjunto do repositório: `LIMIT` só em item com `ordem_importa`.
- **`SQL_CATEGORIAS`** agora existe em `src/agent/agente.py` e em `src/eval/validar_gabarito.py`.
  Pela regra de três, ainda não foi extraído.

## /review (2026-11-13)

Nenhum achado bloqueante. Três achados de severidade baixa foram corrigidos com TDD (335 testes
verdes):
1. O gabarito passa pelo `sql_guard` já no schema. Antes só a sintaxe era checada na carga, e
   `DELETE` ou dois comandos só eram barrados pelo teste H2.
2. Arquivo fora de UTF-8 vira `ConjuntoInvalido`, em vez de `UnicodeDecodeError` cru.
3. O comando trata conjunto inválido (saída 1) e erro de SQL ao listar as categorias (saída 2), sem
   traceback.

Um quarto ponto ficou como limitação conhecida: "valor não nulo" aceita `0`. Com o banco vazio,
`COUNT(*)` passa. As somas falham nesse caso, então a execução ainda termina com código 1.

## Pendências (não bloqueantes)

- [ ] **"Partido/UF da época" não existe nos dados.** O CSV da CEAP repete o partido e a UF atuais em
      todas as linhas do deputado: no banco, `despesas.partido` nunca difere de `deputados.partido`.
      A regra 6 da Constituição e o prompt do agente assumem o contrário. Decidir se:
      - a regra vira "partido/UF do cadastro";
      - ou se a ingestão busca o histórico de filiação na API de Dados Abertos.
- [ ] **Lideranças têm `uf = 'NA'`** (e `partido` nulo), e o prompt não diz isso. Uma pergunta "por
      UF" do agente traz a linha `NA`. Avaliar uma regra no prompt ou um few-shot (bloco 4).
