# Spec BDD: {STORY-ID} — {Título}

> **Story**: [link para story.md]
> **Status**: Draft | In Review | Approved
> **Autor**: {nome}
> **Revisores**: {nomes}

---

## Feature: {Nome da Feature}

{Descrição breve da feature e seu valor de negócio.}

### Regras de Negócio

<!-- Liste as regras que governam esta feature. Estas regras serão validadas nos cenários. -->

1. {Regra 1}
2. {Regra 2}
3. {Regra 3}

---

### Cenários — Happy Path

```gherkin
Scenario: {Descrição do cenário principal}
  Given {contexto/pré-condição}
  And {contexto adicional}
  When {ação do usuário/sistema}
  Then {resultado esperado}
  And {resultado adicional}
```

```gherkin
Scenario: {Outro cenário de sucesso}
  Given {contexto}
  When {ação}
  Then {resultado}
```

---

### Cenários — Edge Cases

```gherkin
Scenario: {Cenário de borda}
  Given {contexto atípico}
  When {ação}
  Then {comportamento esperado na borda}
```

---

### Cenários — Error Cases

```gherkin
Scenario: {Cenário de erro}
  Given {contexto que leva ao erro}
  When {ação que falha}
  Then {mensagem/comportamento de erro esperado}
```

---

## Mapping: Cenário → Teste

| Cenário | Arquivo de Teste | Status |
|---------|-----------------|--------|
| {Nome cenário 1} | `tests/{path}` | 🔴 Red / 🟢 Green |
| {Nome cenário 2} | `tests/{path}` | 🔴 Red / 🟢 Green |
| {Nome cenário 3} | `tests/{path}` | 🔴 Red / 🟢 Green |

---

## Notas de Especificação

<!-- Ambiguidades resolvidas, decisões de escopo, referências -->
