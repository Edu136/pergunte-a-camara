# Spec 01 — Agente de consultas

**Status:** rascunho · **Versão:** 0.1 · **Depende de:** [00-princípios](00-principios.md)

## 1. Objetivo

Responder perguntas em português sobre os gastos da cota parlamentar (CEAP), mostrando os dados,
um gráfico e uma explicação, com cada passo do raciocínio do agente visível na interface.

## 2. Exemplos de perguntas

- "Quanto os deputados de MG gastaram com passagens aéreas em 2025?"
- "Como evoluíram os gastos com combustíveis mês a mês em 2024?"
- "Quais as 5 categorias com maior gasto total em 2025?"
- "Divulgação de atividade parlamentar pode ser reembolsada?" (RAG nas normas)
- "Há despesas fora do padrão em locação de veículos em 2025?" (anomalias)

## 3. Ferramentas do agente

| Ferramenta | O que faz |
|---|---|
| `consultar_sql` | Gera SQL a partir da pergunta, valida (P3) e executa com usuário somente leitura |
| `buscar_normas` | Busca vetorial nos trechos das normas da CEAP (RAG) |
| `detectar_anomalias` | Aponta valores fora do padrão por categoria (ex.: z-score ou IQR) |
| `gerar_grafico` | Escolhe o tipo de gráfico adequado ao formato dos dados |

## 4. Fluxo

1. O agente lê a pergunta e decide quais ferramentas usar (máx. `AGENTE_MAX_PASSOS` passos).
2. Cada chamada de ferramenta vira um `PassoAgente`, exibido em tempo real.
3. Se o SQL falhar na validação ou na execução, o agente recebe o erro e tenta corrigir
   (até 2 tentativas).
4. A resposta final segue o contrato `Resposta` de `src/schemas.py`.

## 5. Regras de negócio

- **RN01:** a resposta sempre inclui o SQL executado, quando houver.
- **RN02:** perguntas fora do escopo (ex.: "quem vai ganhar a eleição?") retornam
  `respondida = false` com explicação educada.
- **RN03:** pedidos de opinião ou juízo sobre deputados e partidos são recusados (P1).
- **RN04:** anomalias sempre vêm com o aviso do princípio P1.
- **RN05:** respostas baseadas em normas citam a fonte (`fontes`).

## 6. Critérios de aceite

- [ ] As 5 perguntas de exemplo são respondidas com dados corretos.
- [ ] Os comandos perigosos de `tests/test_sql_guard.py` são bloqueados.
- [ ] Uma pergunta fora do escopo retorna `respondida = false`.
- [ ] Um pedido de opinião é recusado de forma neutra.
- [ ] Acurácia de execução ≥ 80% no conjunto de avaliação (spec 02, a escrever).

## 7. Fora do escopo (por enquanto)

- Dados do Senado e de assembleias estaduais.
- Deploy em nuvem.
