# ADR-001: O agente escreve o SQL e cada passo é registrado em detalhe

> **Data**: 2026-10-28
> **Status**: Accepted
> **Story**: STORY-001
> **Decisores**: Edu136

## Contexto

A spec 01 descrevia `consultar_sql` como "gera SQL a partir da pergunta", sem dizer quem gera.
Além disso, `PassoAgente` tinha só `ferramenta`, `descricao` e `sucesso`, insuficiente para a demo
mostrar o que aconteceu, para a autocorreção ser auditável e para o log JSONL alimentar a avaliação
(CA5). Os dois pontos mudam o contrato `Resposta`, o que pelos acordos do time exige ADR.

## Opções Consideradas

### Opção A: O LLM do agente escreve o SQL como argumento da ferramenta (`consultar_sql(sql)`)

- **Prós**: uma chamada ao LLM por passo; o erro do guard ou do banco volta como resultado da
  ferramenta e o próprio modelo corrige; o raciocínio fica visível num só lugar.
- **Contras**: o prompt do agente precisa carregar o schema e as categorias (pressão na janela de
  contexto).

### Opção B: A ferramenta recebe uma sub-pergunta e chama outro LLM para gerar o SQL

- **Prós**: prompt do agente menor; especialização do gerador de SQL.
- **Contras**: duas chamadas ao LLM por passo (lento num 7B local); a correção acontece longe do
  raciocínio do agente; mais código para testar.

## Decisão

Escolhemos **Opção A**, e `PassoAgente` passa a ter:

| Campo | Tipo | Descrição |
|---|---|---|
| `ferramenta` | str (antes Literal) | Nome da ferramenta chamada — `str` para registrar também chamadas a ferramentas desconhecidas |
| `descricao` | str (inalterado) | Texto curto para a interface |
| `entrada` | dict | Argumentos recebidos (ex.: `{"sql": "..."}`) |
| `saida` | str \| None | Resumo da saída (ex.: "12 linhas") |
| `erro` | str \| None | Motivo da falha, quando houver |
| `duracao_ms` | int | Tempo da execução da ferramenta |
| `sucesso` | bool (inalterado) | Se a chamada deu certo |

Os campos novos têm valor padrão, então o contrato continua compatível com quem só lê os antigos.

## Consequências

### Positivas

- Autocorreção simples e natural no loop.
- A demo, o log JSONL e a avaliação usam o mesmo objeto.

### Negativas

- Prompt de sistema maior → exige `OLLAMA_NUM_CTX` configurado.
- A spec 01 precisa ser ajustada para refletir que o SQL vem do agente.

### Riscos

- Estourar a janela de contexto → `OLLAMA_NUM_CTX` e no máximo `AGENTE_LINHAS_PARA_LLM` linhas devolvidas ao modelo.
- `entrada` conter dado sensível no log → só há SQL e dados públicos; CPF nunca chega ao banco (P4).

## Referências

- `specs/STORY-001/analysis.md` (D1, D5)
- `specs/01-agente-consultas.md`
