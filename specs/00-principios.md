# Spec 00 — Princípios do projeto

> Projeto desenvolvido com **Spec-Driven Development (SDD)**: cada funcionalidade começa por uma
> especificação neste diretório, e o código e os testes são escritos a partir dela.

Os princípios **P1 (Neutralidade)**, **P2 (Fidelidade aos dados)**, **P3 (Segurança)** e
**P4 (Privacidade/LGPD)**, junto com as demais regras de domínio, agora vivem na
**[Constituição do projeto](../.sdd/PROJECT-CONSTITUTION.md)**, seção 2. Ela é a fonte de verdade;
as specs continuam citando P1–P4 pelos mesmos códigos.

## Fontes oficiais

| Dado | Fonte |
|---|---|
| Deputados | API de Dados Abertos da Câmara: `dadosabertos.camara.leg.br/api/v2/deputados` |
| Despesas (CEAP) | Arquivos anuais `camara.leg.br/cotas/Ano-{ano}.csv.zip` |
| Normas da CEAP | Atos da Mesa publicados pela Câmara (para o RAG) |
