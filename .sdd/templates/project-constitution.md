# Constituição: {NOME-DO-PROJETO}

> Gerada em: {DATA} | Versão: 1.0
> Gerada por: `/init` — SDD Kit

---

## 1. Identidade

| Campo | Valor |
|-------|-------|
| **Projeto** | {nome} |
| **Problema** | {o problema que resolve — na voz do usuário} |
| **Usuário principal** | {persona + escala esperada} |
| **Tipo** | {MVP / produto em crescimento / ferramenta interna / API pública / migração} |
| **Horizonte** | {prazo de entrega ou entrega contínua} |

---

## 2. Lei do Domínio

> Princípios específicos *deste* projeto. Cada um deve ser específico o suficiente para orientar uma decisão de implementação concreta.

1. **{Princípio 1}** — {explicação em uma frase}
2. **{Princípio 2}** — {explicação em uma frase}
3. **{Princípio 3}** — {explicação em uma frase}

*Exemplo de princípio bom: "Um pedido nunca é deletado — apenas cancelado com razão registrada (auditoria fiscal)"*
*Exemplo de princípio ruim: "Dados devem ser consistentes" (genérico demais)*

---

## 3. Mandatos de Qualidade

> Derivados dos riscos e restrições declarados. O que não pode falhar neste projeto?

### Invioláveis (bloqueiam entrega)
- {mandato 1}
- {mandato 2}

### Críticos (revisados em todo PR)
- {mandato 3}
- {mandato 4}

### Desejáveis (metas, não bloqueadores)
- {mandato 5}

---

## 4. Técnicas Prioritárias

> Selecionadas do PLAYBOOK com base na stack e tipo de produto.

### Patterns a priorizar neste projeto
| Pattern | Razão |
|---------|-------|
| {pattern 1} | {por que se aplica aqui} |
| {pattern 2} | {por que se aplica aqui} |

### Anti-patterns críticos neste contexto
| Anti-pattern | Risco específico |
|-------------|-----------------|
| {anti-pattern 1} | {o que pode dar errado aqui} |
| {anti-pattern 2} | {o que pode dar errado aqui} |

---

## 5. Fronteiras e Integrações

> Onde este sistema se conecta com o mundo externo.

| Sistema | Tipo | Responsabilidade | Risco |
|---------|------|-----------------|-------|
| {integração 1} | {API / fila / webhook / DB} | {o que esta integração faz} | {o que pode falhar} |

---

## 6. Acordos do Time

> Calibrado pelo perfil e tamanho da equipe.

- **Nível de abstração**: {ex: mínimo necessário — time pequeno prefere clareza a elegância}
- **Revisão de código**: {ex: todo PR revisado por pelo menos 1 pessoa}
- **Decisões arquiteturais**: {ex: qualquer mudança que afete 2+ módulos → ADR obrigatório}
- **Frequência de /sync**: {ex: após cada refactor significativo}

---

## 7. Emendas

> Atualizações à Constituição devem ser versionadas e datadas. Uma emenda não apaga o princípio anterior — registra a evolução.

| # | Data | Mudança | Razão |
|---|------|---------|-------|
| — | — | — | — |

---

## 8. Fitness Functions

> Condições arquiteturais mensuráveis e automatizáveis. Diferente dos Mandatos de Qualidade (seção 3, critérios humanos), Fitness Functions são executáveis por sensores computacionais — elas passam ou falham.
>
> Calibre os limiares ao perfil do projeto. Uma FF irrealista é ignorada; uma FF ausente não protege.

| # | Função | Limiar | Sensor | Frequência |
|---|--------|--------|--------|------------|
| FF-001 | Cobertura de testes | ≥ {X}% | coverage tool | pre-commit |
| FF-002 | Complexidade ciclomática | ≤ {N} por função | linter | pre-commit |
| FF-003 | Tamanho de módulo | ≤ {N} linhas | linter | pre-commit |
| FF-004 | Dependências proibidas entre camadas | 0 violações | constraint test | CI |
| FF-005 | Drift spec ↔ código | 0 cenários desincronizados | /sync | pós-merge |

> Adicione FFs específicas ao domínio:
> - ex: "Tempo de resposta P95 ≤ 200ms" para APIs de alta performance
> - ex: "0 secrets detectados em código" para projetos com requisitos de compliance
> - ex: "Toda mutation do domínio tem fixture aprovada" para sistemas financeiros
