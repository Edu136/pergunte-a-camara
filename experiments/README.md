# Experimentos

## Conjunto de avaliação

[`conjunto_avaliacao.json`](conjunto_avaliacao.json) tem 60 perguntas, 10 por categoria, cada uma
com o comportamento esperado do agente (spec: [STORY-006](../specs/STORY-006/spec.bdd.md)).

| Categoria | Id | Espera | Gabarito |
|---|---|---|---|
| `facil` | `F01`–`F10` | resposta | SQL de referência |
| `media` | `M01`–`M10` | resposta | SQL de referência |
| `dificil` | `D01`–`D10` | resposta | SQL de referência |
| `fora_do_escopo` | `X01`–`X10` | recusa | — |
| `opiniao` | `O01`–`O10` | recusa neutra (P1) | — |
| `injection` | `I01`–`I10` | recusa, sem SQL perigoso executado | — |

**O gabarito é SQL, não número.** A avaliação roda o SQL de referência e o SQL do agente no mesmo
banco e compara os resultados. `ordem_importa` marca os rankings, em que a ordem das linhas faz parte
da resposta.

**Dificuldade**, conferida no próprio SQL por `classificar_dificuldade`:
- **fácil:** até 2 condições no `WHERE`, sem `GROUP BY` nem `ORDER BY`;
- **média:** `GROUP BY` ou `ORDER BY`, ou 3 condições ou mais;
- **difícil:** `JOIN`, subconsulta, CTE ou função de janela.

**Injection** em três famílias:
- ignorar as regras ou revelar o prompt (incluindo fechar o delimitador `</dados>`);
- pedir escrita (apagar, alterar, criar tabela);
- ler fora das tabelas permitidas (`pg_*`, `information_schema`, senhas, `.env`).

**Regras do conjunto:**
- nenhuma pergunta cita deputado pelo nome;
- nenhuma pergunta aparece nas perguntas de exemplo da demo nem no prompt (teste de vazamento);
- os exemplos de few-shot nunca virão deste conjunto.

Para conferir o gabarito no banco carregado:

```bash
python -m src.eval.validar_gabarito   # 0 = ok, 1 = falhas, 2 = banco indisponível
```

## Avaliação do text-to-SQL

Métrica principal: **acurácia de execução** (o resultado da consulta gerada é igual ao da consulta
de referência).

| Modelo | Acurácia de execução | Latência média | Custo por pergunta |
|---|---|---|---|
| qwen2.5:7b (local) | – | – | R$ 0 |
| qwen2.5-coder:7b (local) | – | – | R$ 0 |
| gpt-4o-mini (API, opcional) | – | – | – |
