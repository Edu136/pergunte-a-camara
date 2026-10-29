# Story: STORY-002 — Validar categorias citadas no SQL e sinalizar resultado vazio

## Descrição

Como **cidadão curioso ou jornalista de dados**,
Quero **que o agente acerte o nome exato da categoria de despesa mesmo quando eu (ou o modelo)
escrevo de forma aproximada**,
Para que **eu não receba "nenhum gasto" só porque faltou um ponto no nome da categoria**.

## Contexto

Achado do primeiro teste com dados reais (STORY-001): para "Quanto os deputados de MG gastaram com
combustíveis em 2025?", o modelo gerou `categoria = 'COMBUSTÍVEIS E LUBRIFICANTES'`, mas o texto
oficial é `'COMBUSTÍVEIS E LUBRIFICANTES.'` (com ponto). A consulta rodou, o `SUM` voltou `NULL` e
o agente tratou como sucesso. Outras categorias têm o mesmo tipo de detalhe
(`DIVULGAÇÃO DA ATIVIDADE PARLAMENTAR.`, `HOSPEDAGEM ,EXCETO ...`).

Normalizar os textos na ingestão violaria o princípio 7 (categorias pertencem à Câmara). A saída é
validar o valor antes de executar e devolver uma sugestão ao modelo, usando a autocorreção que já
existe. Princípios em jogo: P2 (fidelidade), 7 (categorias da Câmara).

## Critérios de Aceite

- [ ] **CA1 — Categoria inexistente não executa:** se o SQL compara `categoria` com um texto que não
      está entre as categorias reais (`=`, `IN`, `<>`/`!=`), a consulta não vai ao banco e o modelo
      recebe um erro corrigível com até 3 categorias parecidas.
- [ ] **CA2 — Categoria exata executa:** textos idênticos aos oficiais (com pontuação) seguem normalmente.
- [ ] **CA3 — Diferença só de maiúsculas também é erro:** o `=` do Postgres diferencia maiúsculas,
      então `'combustíveis e lubrificantes.'` é rejeitado, com a sugestão do texto oficial.
- [ ] **CA4 — Sem lista, sem validação:** se as categorias não puderam ser carregadas (E7 da
      STORY-001), a validação é ignorada e a consulta segue.
- [ ] **CA5 — Conta como falha corrigível:** a rejeição usa o mesmo contador de correções da STORY-001.
- [ ] **CA6 — Resultado vazio sinalizado ao modelo:** quando a consulta não traz linhas, ou só traz
      valores nulos (ex.: `SUM` sem registros), o resultado devolvido ao modelo diz explicitamente que
      nenhum registro foi encontrado e que não deve informar valores.

## Estimativa

- **Tamanho**: P
- **Complexidade**: Baixa

## Dependências

| Tipo | Descrição | Status |
|------|-----------|--------|
| Story | STORY-001 (agente, categorias no prompt, autocorreção) | Concluída |

## Notas

- Fora do escopo: validar outras colunas (`uf`, `partido`, `subcategoria`). Avaliar no bloco 3
  se aparecem erros parecidos.
- `LIKE`/`ILIKE` com padrão não são validados (o modelo escolheu busca aproximada de propósito).
