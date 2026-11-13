# Análise: STORY-006 — Conjunto de avaliação rotulado por categoria

## 1. Código relevante

| Peça | Onde | Uso nesta story |
|---|---|---|
| `validar_sql` | `src/tools/sql_guard.py` | CA4: todo SQL de referência passa pelo guard (teste sem banco). |
| `ConsultorSQL` | `src/tools/consultar_sql.py` | CA5: executa o gabarito com `agente_leitura`, `READ ONLY` e `statement_timeout`. Reaproveitado sem mudança. |
| `validar_categorias` | `src/tools/validar_categorias.py` | CA5: confere se o texto de categoria do gabarito existe no banco. |
| `Pergunta` | `src/schemas.py` | CA2: mesmo limite de 5–500 caracteres da API. |
| `PERGUNTAS_EXEMPLO` | `app/streamlit_app.py` | CA7: comparação para o teste de vazamento. |
| `PROMPT_SISTEMA` | `src/agent/prompts.py` | CA7: idem. |
| FF-004 | `tests/test_arquitetura.py` | O módulo novo de avaliação entra na lista de pastas que só podem usar a conexão de leitura. |
| CLI | `src/ingestion/__main__.py` | Padrão a seguir para o comando do CA5 (`argparse` + `logging`). |

Nada existe ainda em `src/eval/`. `experiments/README.md` só tem a tabela de resultados vazia.

## 2. Domínio

- **Conceitos novos:** item de avaliação, categoria de avaliação, gabarito (SQL de referência),
  comportamento esperado (`respondida`). São dados de apoio, não entidades do domínio da CEAP.
- **Regras explícitas:** P1 (opinião → recusa neutra), P2 (o gabarito é SQL executado, nunca um
  número escrito à mão), P3 (gabarito passa pelo guard e roda como leitura), princípio 10 (few-shot
  nunca sai do conjunto).
- **Regras implícitas que o gabarito precisa respeitar** (senão o gabarito ensina errado):
  - somar `valor_liquido`, sem filtrar negativos (regra 5);
  - partido/UF da época vêm de `despesas` (regra 6);
  - textos de categoria exatos da Câmara (regra 7);
  - perguntas sobre deputados excluem `deputado_id` nulo (liderança).
- **O gabarito não guarda resultados.** O harness roda o SQL de referência e o SQL do agente no mesmo
  banco e compara. Assim o conjunto não fica velho se a carga mudar, e nenhum número é escrito à mão
  (P2).

## 3. Direção

**Módulo novo `src/eval/`** (previsto na Constituição, seção 6), com duas peças pequenas:

- `src/eval/conjunto.py`: schema Pydantic (`ItemAvaliacao`, `ConjuntoAvaliacao`), `carregar_conjunto()`
  e a regra de consistência categoria ↔ comportamento.
- `src/eval/__main__.py` (ou `validar_gabarito.py`): comando do CA5,
  `python -m src.eval.validar_gabarito`, que roda o gabarito no banco e lista as falhas.

**Arquivo de dados: `experiments/conjunto_avaliacao.json`** (lista de objetos). Motivos:
- JSON é stdlib (YAML exigiria dependência nova) e segue a convenção de fixtures `.json`;
- fica ao lado dos resultados publicados, que é onde o leitor do portfólio procura;
- um objeto por item com `sql` em string única é legível o bastante para ~30 SQLs.

**Formato do item** (proposta):

```json
{
  "id": "M03",
  "categoria": "media",
  "pergunta": "Quais as 5 categorias com maior gasto em 2025?",
  "respondida": true,
  "sql": "SELECT categoria, SUM(valor_liquido) AS total FROM despesas WHERE ano = 2025 GROUP BY categoria ORDER BY total DESC LIMIT 5",
  "ordem_importa": true,
  "nota": "Regressão da STORY-005: virou LIMIT 1."
}
```

- `id`: prefixo da categoria + número (`F`, `M`, `D`, `X` fora do escopo, `O` opinião, `I` injection).
- `ordem_importa`: só o que afeta o gabarito. Em rankings a ordem faz parte da resposta; no resto o
  harness compara como conjunto. Nomes de coluna e arredondamento ficam para o harness decidir, sem
  campo no arquivo.
- Consistência validada no schema: `facil|media|dificil` ⇒ `respondida = true` e `sql` presente;
  as outras ⇒ `respondida = false` e `sql` ausente. Ids únicos no conjunto.

**Regra de dificuldade (CA6)**, escrita na spec e checada por inspeção do SQL (sqlglot):
- **fácil:** uma tabela, uma agregação, até 1 filtro, sem `GROUP BY`;
- **média:** `GROUP BY` e/ou ranking (`ORDER BY … LIMIT`), ou 2+ filtros;
- **difícil:** pelo menos um entre: `JOIN`, subconsulta/CTE, função de janela, comparação entre anos
  na mesma consulta, percentual sobre o total.

Checar a regra por código (contando nós do sqlglot) evita rótulo no achismo. É um teste pequeno; se
ficar frágil, vira só regra escrita + revisão.

**Teste de vazamento (CA7):** normaliza texto (minúsculas, sem acento, sem pontuação) e verifica que
nenhuma pergunta do conjunto está em `PERGUNTAS_EXEMPLO` nem dentro de `PROMPT_SISTEMA`.
`PERGUNTAS_EXEMPLO` é lida do arquivo da página por `ast` (importar a página executa o Streamlit).
A função de normalização/vazamento fica em `src/eval/conjunto.py` para o few-shot do bloco 4 reusar.

**Tamanho:** 60 itens, 10 por categoria. 30 SQLs de referência são viáveis de escrever e conferir à
mão; dá margem para a acurácia ter resolução de ~3 pontos por pergunta por categoria respondível.

**Cobertura de injection** (10 itens), em três famílias:
- instrução na pergunta para ignorar regras / revelar o prompt;
- pedido que exige escrita (apagar, alterar, criar tabela) disfarçado de pergunta;
- tentativa de ler fora das tabelas permitidas (`pg_*`, `information_schema`, senhas, `.env`).

Todos esperam `respondida = false`. "Bloqueio ponta a ponta" (nenhum SQL perigoso executado) é métrica
do harness, a partir dos passos; o conjunto só marca a categoria.

## 4. Fronteiras de escopo

- **Dentro:** arquivo com 60 itens, schema, testes de CI (schema, guard, dificuldade, vazamento),
  comando do CA5, regra de dificuldade documentada, FF-004 cobrindo `src/eval/`.
- **Fora:** rodar o agente, métricas, relatório, comparação de modelos (próximos itens do bloco 3).
- **Fora (ambíguo, evitado):** perguntas de anos sem dados (ex.: 2019). O agente pode consultar,
  achar nada e dizer isso, o que é um comportamento correto e não uma recusa. Ficam para quando o
  harness tiver o caso "respondida sem dados".

## 5. Riscos e casos de borda

| Risco | Impacto | Mitigação |
|---|---|---|
| Docker parado agora | Não dá para confirmar os textos de categoria nem rodar o CA5 | Escrever o gabarito com o banco no ar; o CA5 é o sensor. |
| Gabarito errado (SQL que não responde a pergunta) | Mede o agente contra uma resposta errada | Revisão manual + CA5 exigindo linha não nula; `nota` no item quando houver escolha de interpretação. |
| Timeout de 5 s com cache frio (visto na STORY-005) | CA5 falha sem o SQL estar errado | O comando mostra o tempo de cada consulta; o gabarito deve rodar com folga. Registrar se a falha some na 2ª execução. |
| Pergunta ambígua (ex.: "gasto" bruto ou líquido) | Agente "erra" com resposta defensável | O gabarito sempre segue as regras do prompt (líquido, época); pergunta com duas leituras razoáveis é reescrita. |
| Regra de dificuldade por código ficar frágil | Teste quebra por estilo de SQL | Contar só nós claros (`Join`, `Subquery`, `CTE`, `Window`, `Group`); se não estabilizar, rebaixar para revisão manual. |
| Opinião vs. ranking neutro | "Quem gastou mais?" é neutro (P1 permite ranking por valor); "Quem desperdiça mais?" é opinião | A spec dá pares de exemplo; rankings neutros entram como `media`. |
| Gabarito com nome de deputado | Viola P1 (demo e post não citam nomes) | Perguntas sem nomes; resultados podem trazer nomes, mas o arquivo não. |
| `src.eval` como nome de pacote | Confusão com o builtin `eval` | Só é usado como caminho de módulo (`src.eval`), sem conflito real. |

Não há decisão arquitetural que peça ADR: nenhuma dependência nova, sem mudança em segurança nem no
contrato `Resposta`. Blueprint: o fluxo do CA5 tem 3 passos (carregar → guard → executar), então cabe
um diagrama curto.
