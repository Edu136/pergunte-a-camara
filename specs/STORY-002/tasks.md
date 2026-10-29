# Tasks: STORY-002 — Validar categorias citadas no SQL e sinalizar resultado vazio

> **Story**: [story.md](story.md)
> **Spec**: [spec.bdd.md](spec.bdd.md)

## Tasks

### Task 1: Validador de categorias

- **Cenários BDD**: H1, E1, E2, E3, E4, X1
- **Tipo**: feature
- **Dependência**: —
- **Critério de conclusão**: `validar_categorias` e `CategoriaInexistente` com testes verdes
- **Status**: ✅ Concluída

### Task 2: Integração no agente

- **Cenários BDD**: H2, X2
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: validação antes de `consultar`, usando as categorias em cache
- **Status**: ✅ Concluída

### Task 3: Aviso de resultado vazio

- **Cenários BDD**: E5
- **Tipo**: feature
- **Dependência**: —
- **Critério de conclusão**: `formatar_dados` sinaliza 0 linhas e linhas só com nulos
- **Status**: ✅ Concluída

### Task 4: Sync e documentação

- **Cenários BDD**: —
- **Tipo**: docs
- **Dependência**: Tasks 1–3
- **Critério de conclusão**: blueprint da STORY-001 com a validação; ruff e pytest verdes
- **Status**: ✅ Concluída

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4
```

## Progresso

- Total: 4 tasks
- Concluídas: 4/4
- Cenários BDD cobertos: 10/10 (9 originais + E6 adicionado no TDD)

## Notas do Sync

- **E6 (adicionado):** testando com as 21 categorias reais, `'COMBUSTÍVEIS'` não recebia sugestão
  (o difflib compara a string inteira e textos curtos ficam abaixo do limite). Agora as categorias
  que **contêm** o texto vêm primeiro nas sugestões.
- Validação com dados reais: o SQL do log (`'COMBUSTÍVEIS E LUBRIFICANTES'`) é barrado sugerindo
  `'COMBUSTÍVEIS E LUBRIFICANTES.'`; o valor correto (MG, 2025) é R$ 2.646.274,41.
- Validação com o Ollama real (qwen2.5:7b, CPU): o modelo errou a categoria, recebeu a sugestão e
  corrigiu na tentativa seguinte (log de 2026-10-28, 23:58 → 23:59).

## Pendências do /review (não bloqueantes)

- [ ] Recarregar a lista de categorias uma vez antes de rejeitar (hoje o cache dura o processo
      inteiro e, com a API no ar, uma categoria nova seria barrada até reiniciar).
- [ ] Sugestão por "texto contido" só para textos com 4+ caracteres (`'A'` sugere 3 categorias sem sentido).
- [ ] Falso positivo quando um alias se chama `categoria` (ex.: `uf AS categoria`) — raro; só registrar.
- [ ] Sugestões (nomes de categoria do banco) voltam ao modelo fora de `<dados>` — risco baixo (P9).
