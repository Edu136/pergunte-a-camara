# Tasks: STORY-003 — Gráfico adequado ao formato dos dados

> **Story**: [story.md](story.md)
> **Spec**: [spec.bdd.md](spec.bdd.md)

## Tasks

### Task 1: Configuração e CI

- **Cenários BDD**: base (E5)
- **Tipo**: setup
- **Dependência**: —
- **Critério de conclusão**: `GRAFICO_MAX_BARRAS` em `Settings` e `.env.example`; `plotly` instalado no CI
- **Status**: ✅ Concluída

### Task 2: `escolher_grafico`

- **Cenários BDD**: H1, H2, E1–E7, E9, X1, X3
- **Tipo**: feature
- **Dependência**: Task 1
- **Critério de conclusão**: regras RN1–RN8 com testes verdes, sem importar plotly
- **Status**: ✅ Concluída

### Task 3: `montar_figura`

- **Cenários BDD**: H4, H5, E8, E10
- **Tipo**: feature
- **Dependência**: Task 2
- **Critério de conclusão**: skill `dataviz` consultada; figura com R$/pt-BR (RN9); testes verdes
- **Status**: ✅ Concluída

### Task 4: Integração no agente

- **Cenários BDD**: H3, X2
- **Tipo**: feature
- **Dependência**: Task 2
- **Critério de conclusão**: `Resposta.grafico` preenchido e passo `gerar_grafico` (RN10)
- **Status**: ✅ Concluída

### Task 5: Documentação e sync

- **Cenários BDD**: —
- **Tipo**: docs
- **Dependência**: Tasks 1–4
- **Critério de conclusão**: spec 01 reflete ADR-002; roadmap marca o item; ruff e pytest verdes
- **Status**: ✅ Concluída

---

## Ordem de Execução

```
Task 1 → Task 2 → Task 3 → Task 4 → Task 5
```

## Progresso

- Total: 5 tasks
- Concluídas: 5/5
- Cenários BDD cobertos: 23/23 (18 originais + E11, E12 no TDD + X4, X5, X6 no /review)

## Notas do Sync

- **E11 e E12 (adicionados):** ao renderizar com dados reais (combustíveis por mês, 2025), o eixo y
  começava em R$ 1,4 mi e fazia uma variação de ~30% parecer queda brusca (risco a P1), e o eixo x
  mostrava só meses pares. Agora o eixo de valores começa em zero e os meses aparecem como jan…dez.
- **Visual conferido** com a skill `dataviz` (série única no slot 1 `#2a78d6`, sem legenda,
  linha 2 px, marcadores 8 px, barras com cantos 4 px, grade recessiva) renderizando PNGs com dados
  reais via `kaleido`, instalado só na `.venv` local (não entra no `requirements.txt`).
- **Testes da STORY-001 ajustados:** contavam o total de passos; com o passo automático
  `gerar_grafico` (RN10), passaram a contar só os passos `consultar_sql`, que é o que os cenários
  H1, H5, E3 e H6 da STORY-001 descrevem.
- **CI:** passou a instalar `plotly`.

## Correções do /review (achadas renderizando com dados reais)

- **X4:** barras por `deputado_id` ficavam invisíveis (eixo x numérico contínuo de 220k a 224k).
  Agora o eixo x de barras é sempre de categorias.
- **X5:** linha por `ano` mostrava `2.024,2`, `2.024,4`… Agora `dtick = 1` e formato inteiro.
- **X6:** a tabela mostrava valores crus (`6619024.49`). A primeira correção usou `format`/`prefix`
  do plotly e o teste passou, mas a imagem mostrou `R$ 6,619,024.49`: o `go.Table` **ignora**
  `layout.separators`. Os valores passaram a ser formatados em Python (pt-BR, espaço sem quebra
  após "R$") e o teste agora confere o **texto exibido**, não a configuração.
- Lição registrada: para figura, conferir a renderização; teste de configuração não basta.

## Pendências do /review (não bloqueantes)

- [ ] Eixo abreviado usa "k" do inglês (`R$ 600k`); o `~s` do d3 não tem localização pt-BR.
- [ ] Gráfico por `deputado_id` é pouco útil ao cidadão: orientar o modelo a agrupar por
      `nome_parlamentar` (prompt/few-shot, bloco 4).
- [ ] Rótulos vindos do banco (ex.: fornecedor) aceitam algumas tags HTML no plotly; fonte é a
      Câmara e o plotly sanitiza links — revisar quando a demo existir.
- Validação manual do autor (2026-10-29): linha, barra e tabela abertas no navegador com dados reais, tudo OK.
