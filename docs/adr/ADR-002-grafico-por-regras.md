# ADR-002: O gráfico é escolhido por regras fixas, não pelo LLM

> **Data**: 2026-10-29
> **Status**: Accepted
> **Story**: STORY-003
> **Decisores**: Edu136

## Contexto

A spec 01 listava `gerar_grafico` entre as ferramentas do agente. No primeiro teste real, o
`qwen2.5:7b` rodando 100% em CPU levou mais de 2 minutos numa única resposta. Uma ferramenta de
gráfico chamada pelo LLM somaria mais uma chamada por pergunta, com risco de eixos inexistentes e de
títulos com juízo de valor (P1).

## Opções Consideradas

### Opção A: Ferramenta `gerar_grafico` chamada pelo LLM

- **Prós**: mais uma ferramenta na vitrine de tool use; o modelo conhece a intenção da pergunta.
- **Contras**: +30–90 s por pergunta em CPU; 7B pode escolher eixos que não existem; título livre
  pode violar P1; testes dependem do comportamento do modelo.

### Opção B: Regras fixas aplicadas pelo agente aos dados da resposta

- **Prós**: latência zero; determinística e 100% testável; título neutro por construção; eixos
  sempre válidos.
- **Contras**: não capta intenções que os dados não revelam (ex.: "proporção" → pizza).

## Decisão

Escolhemos **Opção B**. A escolha aparece como um `PassoAgente` `gerar_grafico` marcado como
automático, para a demo e o log mostrarem a etapa. Pizza nunca é escolhida pelas regras.

## Consequências

### Positivas

- Resposta mais rápida e previsível; P1 e CA5 garantidos sem depender do modelo.

### Negativas

- A spec 01 precisa ser ajustada: `gerar_grafico` deixa de ser ferramenta do LLM.
- Gráficos de proporção ficam de fora até haver *override* pelo LLM.

### Riscos

- Regras não cobrirem um formato comum → cai em `tabela` (seguro). A avaliação (bloco 3) mede
  quais formatos aparecem; um *override* do tipo pelo LLM exigiria novo ADR.

## Referências

- `specs/STORY-003/analysis.md` (D1–D4), `specs/STORY-003/blueprint.mermaid`
