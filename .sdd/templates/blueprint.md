# Blueprint: {STORY-ID} — {Título}

> **Story**: [link para story.md]
> **Tipo**: Fluxo | Sequência | Modelo de Dados | Arquitetura
> **Autor**: {nome}

## Descrição

<!-- O que este diagrama representa e por que é necessário? -->

## Diagrama

<!-- Escolha o tipo de diagrama mais adequado. Exemplos abaixo. -->

### Opção: Fluxo de Processo

```mermaid
flowchart TD
    A[Início] --> B{Decisão}
    B -->|Sim| C[Ação A]
    B -->|Não| D[Ação B]
    C --> E[Fim]
    D --> E
```

### Opção: Diagrama de Sequência

```mermaid
sequenceDiagram
    participant U as Usuário
    participant API as API Gateway
    participant S as Serviço
    participant DB as Database

    U->>API: Request
    API->>S: Forward
    S->>DB: Query
    DB-->>S: Result
    S-->>API: Response
    API-->>U: Response
```

### Opção: Modelo de Dados

```mermaid
erDiagram
    ENTITY_A ||--o{ ENTITY_B : "tem muitos"
    ENTITY_A {
        string id PK
        string name
        datetime created_at
    }
    ENTITY_B {
        string id PK
        string entity_a_id FK
        string value
    }
```

## Notas

<!-- Decisões representadas no diagrama, simplificações feitas, aspectos não representados -->
