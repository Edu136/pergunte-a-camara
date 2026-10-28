# Constituição SDD Kit

> Lei fundamental do projeto. Nenhuma implementação pode violar estes princípios.

## Processo

### 1. Discovery First

Nenhuma spec antes de entender o problema. Discovery precede especificação.

O `/discover` conduz a sessão de exploração do espaço do problema: persona, situação atual, impacto, hipótese e suposições críticas. O output é uma **decisão explícita** — Construir, Validar, Diferir ou Descartar — registrada em `.discovery/{DISC-ID}/`.

Só quando a decisão é **Construir** o `/spec` é acionado. Discovery não produz BDD. Spec não produz código.

### 2. Spec First

Nenhuma linha de código antes da spec BDD aprovada. A spec é o contrato.

A spec BDD é produzida por **Produto & Design** em sessão colaborativa (Three Amigos: produto + design + QA), a partir de um discovery aprovado. O Engineer & QA **consome** a spec — não a escreve. A aprovação da spec pelo produto é o gate que libera a implementação.

### 2. Security First

Engineer & QA é responsável pela segurança da implementação. Segurança não é uma fase — é uma dimensão de todo cenário BDD.

- O sensor computacional (pre-commit hook) bloqueia automaticamente secrets hardcoded e arquivos `.env`.
- O sensor inferencial (`/review`) valida OWASP Top 10 por categoria antes de qualquer merge.
- Nenhum secret pertence ao código. Nenhum input externo é confiável sem validação.

### 3. Test First

Todo cenário BDD gera pelo menos um teste. Ciclo: RED → GREEN → REFACTOR.

### 3. Decision First

Decisões arquiteturais geram ADR. ADRs são imutáveis — novas decisões geram novo ADR com `supersedes`.

### 4. Blueprint First

Fluxos com mais de 2 passos exigem diagrama Mermaid antes da implementação.

### 5. Memory First

Informação relevante fica em `.sdd/memory/`. O assistente consulta antes de agir.

### 6. Harness First

O SDD Kit é um harness para agentes de codificação. A fórmula é:

> **Agent = Model + Harness**

Todo artefato é classificado em uma de duas categorias:

- **Guide (feedforward)** — lido antes da ação; aumenta a probabilidade do agente acertar na primeira tentativa. Exemplos: `CONSTITUTION.md`, `spec.bdd.md`, `PLAYBOOK.md`, `blueprint.mermaid`.
- **Sensor (feedback)** — observa após a ação; detecta desvios e permite autocorreção. Exemplos: testes (TDD), `/review`, `/sync`, linters, type checkers.

Sem guides, o agente não tem contexto para agir bem. Sem sensors, erros se repetem indefinidamente.

## Código

### KISS — Keep It Simple

Solução mais simples que atende a spec. "E se no futuro..." não é justificativa.

### SOLID

S — Single Responsibility. O — Open/Closed. L — Liskov Substitution. I — Interface Segregation. D — Dependency Inversion.

### DRY — Don't Repeat Yourself

Regra de três: primeira vez escreva, segunda anote, terceira extraia.

### Hierarquia

KISS primeiro → SOLID no REFACTOR → DRY quando o padrão estabilizou.

## Artefatos

| Artefato | Local | Formato |
|----------|-------|---------|
| Story, Spec BDD, Tasks | `specs/{story-id}/` | .md |
| Blueprint | `specs/{story-id}/` | .mermaid |
| ADRs | `docs/adr/` | .md |
| Memória | `.sdd/memory/` | .md |
| Fixtures de teste | `tests/fixtures/` | .json |
| Testes | `tests/` | linguagem do projeto |

Todo planejamento DEVE ser persistido em `specs/`. Nada existe apenas na conversa.

## Regras para IA

1. Leia `.sdd/memory/PROJECT.md` antes de qualquer ação.
2. Leia esta Constituição no início de cada sessão.
3. Consulte `.sdd/PLAYBOOK.md` durante REFACTOR e /review.
4. Observe o código existente para entender stack e padrões.
5. Nunca implemente sem spec BDD.
6. TDD é obrigatório.
7. Registre decisões em ADRs.
8. Prefira Mermaid a descrições longas de fluxo.
9. Siga os templates em `.sdd/templates/`.
