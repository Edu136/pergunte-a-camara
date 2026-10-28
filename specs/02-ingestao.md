# Spec 02 — Ingestão dos dados

**Status:** implementada · **Versão:** 0.1 · **Depende de:** [00-princípios](00-principios.md)

## 1. Objetivo

Baixar os arquivos anuais de despesas da cota parlamentar, limpar os dados e carregá-los nas
tabelas `deputados` e `despesas`.

## 2. Fontes

- Despesas: `https://www.camara.leg.br/cotas/Ano-{ano}.csv.zip` (CSV, `;`, UTF-8).
- Fotos (opcional): `https://dadosabertos.camara.leg.br/api/v2/deputados?idLegislatura={n}`.
- O campo `ideCadastro` do CSV é o mesmo `id` da API.

## 3. Regras de limpeza

- **RI01:** linhas duplicadas por completo são removidas (problema já relatado na fonte oficial).
- **RI02:** linhas sem valor líquido, ano, mês, categoria ou nome são removidas.
- **RI03:** apenas CNPJs (14 dígitos) são armazenados; CPFs de pessoa física são descartados (P4).
- **RI04:** valores negativos são mantidos, pois representam compensações de bilhetes aéreos.
- **RI05:** despesas de lideranças ficam com `deputado_id` nulo e o nome da liderança em
  `nome_parlamentar`.
- **RI06:** partido e UF são gravados na despesa (situação na época); a tabela `deputados`
  guarda a situação mais recente.
- **RI07:** valores aceitam ponto ou vírgula como separador decimal.

## 4. Carga

- Recarregar um ano é **idempotente**: as despesas do ano são apagadas e inseridas de novo,
  dentro de uma transação.
- Deputados são inseridos ou atualizados (upsert), sem apagar fotos já existentes.
- A carga usa `COPY` para ser rápida em centenas de milhares de linhas.

## 5. Critérios de aceite

- [x] Regras RI01 a RI07 cobertas por testes (`tests/test_ingestao_transform.py`).
- [x] Download reaproveita arquivo existente (`tests/test_ingestao_download.py`).
- [x] Carga repetida não duplica dados.
- [x] Usuário `agente_leitura` não consegue apagar dados.
- [ ] Rodar com os arquivos reais de 2024 e 2025 e registrar o relatório no README.
