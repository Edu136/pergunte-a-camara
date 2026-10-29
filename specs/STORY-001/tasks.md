# Tasks: STORY-001 — Agente responde perguntas com SQL seguro e autocorreção

> **Story**: [story.md](story.md)
> **Spec**: [spec.bdd.md](spec.bdd.md)

## Tasks

### Task 1: Configuração e contrato `PassoAgente`

- **Cenários BDD**: base para todos (ADR-001, notas da spec)
- **Tipo**: setup
- **Dependência**: —
- **Critério de conclusão**: `Settings` e `.env.example` com as 4 chaves novas; `PassoAgente` com `entrada`, `saida`, `erro`, `duracao_ms` (com padrões); `logs/` no `.gitignore`; testes existentes verdes
- **Status**: ✅ Concluída

### Task 2: `sql_guard` bloqueia funções perigosas

- **Cenários BDD**: X6
- **Tipo**: feature
- **Dependência**: —
- **Critério de conclusão**: X6 verde e suíte antiga do guard verde
- **Status**: ✅ Concluída

### Task 3: Ferramenta `consultar_sql` (executor)

- **Cenários BDD**: E5, X7, X8
- **Tipo**: feature
- **Dependência**: Task 1, Task 2
- **Critério de conclusão**: guard + execução `READ ONLY` com timeout + serialização; `ErroExecucaoSQL` tipado; testes com conexão simulada
- **Status**: ✅ Concluída

### Task 4: Cliente de LLM (Protocol, Ollama, fábrica)

- **Cenários BDD**: H8, X4 (cliente), X5
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: testes com `httpx.MockTransport`; `LLMIndisponivel` em erro de rede
- **Status**: ✅ Concluída

### Task 5: Prompts e formatação dos dados

- **Cenários BDD**: H7, E1
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: prompt de sistema com schema, regras e categorias; bloco `<dados>` truncado
- **Status**: ✅ Concluída

### Task 6: Loop do agente

- **Cenários BDD**: H1, H2, H3, H4, H5, E2, E3, E4, E6, X1, X2, X3, X4
- **Tipo**: feature
- **Dependência**: Tasks 3, 4, 5
- **Critério de conclusão**: todos os cenários verdes com LLM e executor falsos
- **Status**: ✅ Concluída

### Task 7: Registro JSONL

- **Cenários BDD**: H6
- **Tipo**: feature
- **Dependência**: Task 6
- **Critério de conclusão**: uma linha JSON por passo, com id e pergunta
- **Status**: ✅ Concluída

### Task 8: Teste de arquitetura (FF-004)

- **Cenários BDD**: X9
- **Tipo**: test
- **Dependência**: Task 6
- **Critério de conclusão**: teste verde e falharia se `database_url` de escrita fosse usado
- **Status**: ✅ Concluída

### Task 9: Documentação

- **Cenários BDD**: —
- **Tipo**: docs
- **Dependência**: Task 8
- **Critério de conclusão**: spec 01 reflete D1 (o agente escreve o SQL); roadmap marca o item; ruff verde
- **Status**: ✅ Concluída

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5 → Task 6 → Task 7 → Task 8 → Task 9 → Sync
```

## Progresso

- Total: 9 tasks
- Concluídas: 9/9
- Cenários BDD cobertos: 28/28 (23 originais + E7, E8 no TDD + X10, X11, X12 no /review)

## Notas do Sync

- **E7 (adicionado):** a spec não dizia o que fazer se a busca das categorias falhasse. Decisão:
  seguir sem categorias e tentar de novo na próxima pergunta (não derruba o agente).
- **E8 (adicionado):** brecha de P9 achada no TDD — um valor com `</dados>` fechava o delimitador.
  Corrigido escapando `<` no JSON.
- **`PassoAgente.ferramenta` virou `str`** (era `Literal`) para registrar chamadas a ferramentas
  desconhecidas (X2). ADR-001 atualizado.
- **CI:** passou a instalar `psycopg[binary]`, exigido por `consultar_sql`.
- Pendente fora desta story: validar o agente com Ollama e Postgres reais (bloco 3, avaliação).

## Correções do /review

- **X10 (bloqueante):** CTE com `DELETE`/`UPDATE`/`INSERT`, `INTO` e `FOR UPDATE` passavam pelo
  guard (o banco segurava, mas P3 exige as duas camadas). Guard agora rejeita esses nós em
  qualquer ponto da árvore; `set_config` e `current_setting` entraram na lista de funções proibidas.
- **X11:** resposta malformada do Ollama (não JSON, tool_call sem `function`) escapava como
  exceção crua; agora vira `LLMIndisponivel`.
- **X12:** banco fora do ar consumia as correções e expunha host/porta; agora `BancoIndisponivel`
  encerra na hora com mensagem genérica.

## Pendências registradas no /review (não bloqueantes)

- [ ] `UNION` é rejeitado pelo guard (limitação funcional; medir impacto na avaliação).
- [x] Timeout do httpx fixo em 120 s → `OLLAMA_TIMEOUT_S` (padrão 300 s) e `OLLAMA_KEEP_ALIVE` (padrão 30m). Motivo real: no primeiro teste com o modelo 100% em CPU, a resposta passou de 120 s.
- [ ] Fakes de teste importados de `tests/test_agente.py` → mover para `tests/conftest.py`.
- [ ] Texto final vazio após consulta bem-sucedida → definir cenário (hoje `respondida = true` com explicação vazia).
- [ ] Senhas fixas de desenvolvimento (`init.sql`, `docker-compose`, defaults do `config.py`) → rever antes de qualquer hospedagem.
