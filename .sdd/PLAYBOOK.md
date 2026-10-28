# Playbook

> Guia prático de patterns, anti-patterns e refactorings.
> Consulte durante o REFACTOR do TDD e no /review.

---

## Como usar este playbook

| Fase TDD | O que consultar |
|----------|----------------|
| RED | Patterns de teste (seção 4), Approved Fixtures (seção 8) |
| GREEN | Nada — escreva o mínimo. KISS. |
| REFACTOR | Patterns de código (seção 1), anti-patterns (seção 2), refactorings (seção 3) |
| Review | Error handling (seção 5), segurança (seção 6), anti-patterns (seção 2), Harness Layers (seção 7) |
| Configurar sensores | Harness Layers (seção 7), Keep Quality Left (seção 9) |

---

## 1. Patterns de código

### 1.1 Early Return

**Quando**: função tem múltiplos níveis de `if/else` aninhados.

**Errado**:
```
function process(input) {
  if (input) {
    if (input.isValid) {
      if (input.hasPermission) {
        // lógica real enterrada 3 níveis dentro
      }
    }
  }
}
```

**Certo**:
```
function process(input) {
  if (!input) return
  if (!input.isValid) return
  if (!input.hasPermission) return

  // lógica real no nível raiz
}
```

**Princípio**: KISS — elimina complexidade cognitiva.

---

### 1.2 Composição sobre herança

**Quando**: você está prestes a criar uma hierarquia de classes.

**Regra**: se a relação não é claramente "é um" (um Cachorro *é um* Animal), prefira composição ("tem um"). Herança acopla; composição desacopla.

**Sinal de alerta**: classe base com métodos que nem todo filho usa → violação de LSP e ISP.

**Princípio**: SOLID (L + I) + KISS.

---

### 1.3 Strategy Pattern

**Quando**: `if/else` ou `switch` escolhe comportamento baseado em tipo ou configuração.

**Aplicar**: extraia cada comportamento para uma função/classe com a mesma interface. A escolha vira um map ou injeção.

**Princípio**: SOLID (O — aberto para extensão, fechado para modificação).

---

### 1.4 Repository Pattern

**Quando**: lógica de acesso a dados está espalhada no código de negócio.

**Aplicar**: isole o acesso a dados atrás de uma interface. O código de negócio depende da abstração, não do banco.

**Princípio**: SOLID (D — dependency inversion) + testabilidade (mocking fácil no RED).

---

### 1.5 DTO / Value Object

**Quando**: dados trafegam entre camadas sem estrutura definida (dicts soltos, maps genéricos).

**Aplicar**: crie tipos explícitos para dados que cruzam fronteiras. Tipagem previne bugs e documenta o contrato.

**Princípio**: KISS (legibilidade) + SOLID (S — cada tipo tem um propósito).

---

### 1.6 Guard Clause

**Quando**: validações de entrada no início de uma função.

**Aplicar**: valide e falhe rápido antes de qualquer lógica de negócio. Separe validação de processamento.

**Princípio**: SOLID (S) + KISS.

---

### 1.7 Façade

**Quando**: o código cliente precisa orquestrar muitas chamadas para completar uma operação.

**Aplicar**: crie uma interface simplificada que esconde a complexidade. O cliente faz uma chamada; a façade orquestra.

**Princípio**: KISS (superfície simples) + SOLID (S — a façade só orquestra).

---

### 1.8 Null Object / Optional

**Quando**: checks de null/undefined espalhados pelo código.

**Aplicar**: use um objeto que representa "ausência" com comportamento neutro, ou use o tipo Optional/Maybe da linguagem.

**Princípio**: KISS (remove condicionais) + DRY (remove checks repetidos).

---

## 2. Anti-patterns

### 2.1 God Class / God Function

**Sintoma**: classe ou função que faz tudo. Mais de ~100 linhas. Precisa de "e" para descrever o que faz.

**Violação**: SOLID (S).

**Correção**: extraia responsabilidades em classes/funções menores. Cada uma faz uma coisa.

---

### 2.2 Shotgun Surgery

**Sintoma**: uma mudança de requisito exige alterar 5+ arquivos.

**Violação**: SOLID (S) — responsabilidade espalhada.

**Correção**: agrupe a lógica relacionada. Se um requisito muda, idealmente um único módulo muda.

---

### 2.3 Feature Envy

**Sintoma**: função acessa mais dados de outro módulo do que do próprio.

**Violação**: SOLID (S) — a lógica está no lugar errado.

**Correção**: mova a função para o módulo cujos dados ela mais usa.

---

### 2.4 Primitive Obsession

**Sintoma**: usar strings, números e booleans para representar conceitos de domínio. Email como string. Dinheiro como float. Status como string.

**Violação**: KISS (bugs sutis) + DRY (validação repetida).

**Correção**: crie tipos de domínio (Value Objects). Email valida no construtor. Money encapsula moeda + valor.

---

### 2.5 Abstração Prematura

**Sintoma**: interface com uma única implementação. Classe base criada "para o futuro". Framework interno para resolver um problema que apareceu uma vez.

**Violação**: KISS — complexidade sem necessidade comprovada.

**Correção**: delete a abstração. Escreva o código concreto. Quando (se) o segundo caso aparecer, a regra de três do DRY guia a extração.

---

### 2.6 Copy-Paste Programming

**Sintoma**: blocos de código iguais ou quase iguais em múltiplos lugares.

**Violação**: DRY.

**Correção**: extraia para função/módulo compartilhado. Mas respeite a regra de três — duas cópias podem ser coincidência, três são um padrão.

---

### 2.7 Boolean Trap

**Sintoma**: função com parâmetro boolean que muda comportamento. `process(data, true, false)` — impossível saber o que true/false significam.

**Violação**: KISS (ilegível).

**Correção**: separe em duas funções com nomes claros, ou use enum/objeto de opções.

---

### 2.8 Magic Numbers / Strings

**Sintoma**: valores literais no código sem explicação. `if (status === 3)`. `timeout: 86400`.

**Violação**: KISS (ilegível) + DRY (repetido sem rastreabilidade).

**Correção**: extraia para constante com nome descritivo. `STATUS_APPROVED = 3`. `ONE_DAY_IN_SECONDS = 86400`.

---

### 2.9 Anemic Domain Model

**Sintoma**: classes que são só dados (getters/setters) com toda lógica em "services" externos.

**Violação**: SOLID (S — a responsabilidade está separada dos dados).

**Correção**: mova a lógica que manipula os dados para dentro da classe que os contém.

---

### 2.10 Over-engineering

**Sintoma**: solução genérica para problema específico. "E se precisarmos suportar 10 provedores de pagamento?" quando há um. Camadas de abstração que ninguém navega.

**Violação**: KISS.

**Correção**: resolva o problema de hoje. Quando o segundo provedor chegar, refatore. O custo de refatorar é menor que o custo de manter abstração desnecessária.

---

## 3. Catálogo de refactorings

> Use durante a fase REFACTOR do TDD. Todos os testes devem continuar verdes.

### 3.1 Extract Function

**Quando**: bloco de código dentro de uma função que faz algo específico e pode ser nomeado.

**Sinal**: comentário explicando o que o bloco faz → o nome da função extraída substitui o comentário.

---

### 3.2 Extract Variable

**Quando**: expressão complexa que dificulta a leitura.

**Aplicar**: atribua a expressão a uma variável com nome descritivo.

---

### 3.3 Rename

**Quando**: nome não revela intenção. `data`, `result`, `temp`, `x`, `val`, `item`.

**Regra**: se você precisa ler o corpo da função para entender o que a variável contém, o nome está ruim.

---

### 3.4 Inline

**Quando**: função ou variável que não adiciona clareza — o corpo é tão claro quanto o nome.

**Oposto de**: Extract. Nem toda extração é boa.

---

### 3.5 Move Function / Move Field

**Quando**: feature envy — a função usa mais dados de outro módulo.

**Aplicar**: mova para onde os dados estão.

---

### 3.6 Replace Conditional with Polymorphism

**Quando**: `if/else` ou `switch` baseado em tipo que se repete em múltiplos lugares.

**Aplicar**: Strategy pattern ou polimorfismo direto.

---

### 3.7 Introduce Parameter Object

**Quando**: função recebe 4+ parâmetros que viajam juntos.

**Aplicar**: agrupe em um objeto/struct com nome descritivo.

---

### 3.8 Replace Magic Number with Constant

**Quando**: literal numérico ou string no código.

**Aplicar**: extraia para constante nomeada.

---

### 3.9 Decompose Conditional

**Quando**: condição complexa com `&&`, `||` e negações.

**Aplicar**: extraia a condição para uma função com nome que descreve a regra de negócio.

```
// Antes
if (user.age >= 18 && user.hasDocument && !user.isBanned)

// Depois
if (isEligible(user))
```

---

### 3.10 Replace Nested Conditional with Guard Clauses

**Quando**: `if` dentro de `if` dentro de `if`.

**Aplicar**: early return para cada condição de saída (ver pattern 1.1).

---

## 4. Patterns de teste

### 4.1 Arrange-Act-Assert (AAA)

Todo teste segue a mesma estrutura:

```
// Arrange — prepara o cenário (Given)
// Act     — executa a ação (When)
// Assert  — verifica o resultado (Then)
```

Mapeia diretamente ao Given/When/Then do BDD.

---

### 4.2 Um assert por conceito

Cada teste valida uma coisa. Se o teste falha, você sabe exatamente o que quebrou.

**Exceção**: múltiplos asserts sobre propriedades do mesmo resultado é aceitável.

---

### 4.3 Teste descreve comportamento, não implementação

**Errado**: `test_calls_repository_save_method`

**Certo**: `test_created_user_is_persisted`

O teste deve sobreviver a refactorings internos. Se você muda a implementação sem mudar o comportamento, o teste não deveria quebrar.

---

### 4.4 Fixture com _meta

Dados de teste em JSON sempre com contexto:

```json
{
  "_meta": { "story": "STORY-001", "scenario": "Login válido" },
  "input": { "email": "user@test.com", "password": "valid123" },
  "expected": { "status": 200, "has_token": true }
}
```

Rastreável até a spec BDD.

---

### 4.5 Test Doubles — quando usar cada um

| Tipo | Quando | Exemplo |
|------|--------|---------|
| **Stub** | Precisa controlar o que uma dependência retorna | Stub de API que sempre retorna 200 |
| **Mock** | Precisa verificar que uma dependência foi chamada | Mock de email service, verificar que `send` foi chamado |
| **Fake** | Precisa de implementação funcional mas simplificada | Banco in-memory em vez de PostgreSQL |
| **Spy** | Precisa registrar chamadas sem alterar comportamento | Spy em logger para verificar o que foi logado |

**Regra**: prefira stubs sobre mocks. Mocks acoplam o teste à implementação.

---

### 4.6 Teste de fronteira

Para cada input, teste os limites:

- Valor mínimo permitido
- Valor máximo permitido
- Um abaixo do mínimo
- Um acima do máximo
- Valor nulo/vazio
- Tipo inesperado (se a linguagem permite)

---

### 4.7 Não teste implementação privada

Teste pela interface pública. Se uma função privada precisa de teste direto, ela provavelmente deveria ser extraída para seu próprio módulo.

---

## 5. Patterns de error handling

### 5.1 Fail Fast

Valide inputs no ponto de entrada. Não propague dados inválidos. Guard clauses no início de cada função pública.

---

### 5.2 Erros esperados vs inesperados

| Tipo | Exemplo | Tratamento |
|------|---------|------------|
| **Esperado** | Credenciais inválidas, recurso não encontrado, validação falha | Retorne resultado tipado (Result/Either) ou erro de domínio |
| **Inesperado** | Banco caiu, disco cheio, bug no código | Exceção/panic — log + alerta + resposta genérica ao usuário |

**Regra**: erros esperados fazem parte do fluxo. Erros inesperados são falhas do sistema.

---

### 5.3 Mensagens de erro úteis

Uma boa mensagem de erro tem:

1. **O que aconteceu**: "Email já cadastrado"
2. **Por que falhou**: "O email user@test.com já está associado a uma conta"
3. **O que fazer**: "Use outro email ou recupere sua senha"

**Nunca**: mensagens genéricas ("Erro interno"), stack traces para o usuário, ou informações sensíveis no erro.

---

### 5.4 Erro de domínio tipado

Crie tipos específicos de erro por domínio em vez de usar exceções genéricas:

```
// Errado
throw new Error("User not found")

// Certo
throw new UserNotFoundError(userId)
// ou
return Result.fail(new UserNotFoundError(userId))
```

Erros tipados são tratáveis programaticamente, rastreáveis e testáveis.

---

### 5.5 Logging estruturado

Logs devem ser parseáveis por máquina:

```json
{
  "level": "error",
  "message": "Payment failed",
  "context": {
    "user_id": "abc-123",
    "amount": 99.90,
    "provider": "stripe",
    "error_code": "card_declined"
  }
}
```

**Nunca**: logar dados sensíveis (senhas, tokens, PII sem mascaramento).

---

### 5.6 Retry com backoff

Para falhas transientes (rede, rate limit, serviço indisponível):

1. Primeira tentativa imediata
2. Segunda tentativa após 1s
3. Terceira tentativa após 4s
4. Quarta tentativa após 16s (exponencial)
5. Desista e retorne erro

**Regra**: só retry em erros transientes. Nunca em erros de validação ou negócio.

---

### 5.7 Circuit Breaker

Para dependências externas que podem ficar indisponíveis:

```
CLOSED  → tudo normal, chamadas passam
OPEN    → dependência caiu, chamadas falham imediatamente (sem esperar timeout)
HALF    → testa se voltou, uma chamada passa — se sucesso, CLOSED; se falha, OPEN
```

Evita cascata de falhas. O sistema degrada com graça em vez de travar.

---

## 6. Segurança — OWASP Top 10

> Engineer & QA é responsável pela segurança da implementação. A spec define o comportamento; o Engineer garante que ele seja seguro.
> O sensor computacional (pre-commit hook) detecta automaticamente secrets e padrões perigosos.
> O sensor inferencial (`/review`) valida semântica e intenção.

### Referência rápida — OWASP Top 10 (2021)

| # | Categoria | Sensor automático | Checklist /review |
|---|-----------|-------------------|-------------------|
| A01 | Broken Access Control | ✗ (inferencial) | ✓ |
| A02 | Cryptographic Failures | ✓ pre-commit (secrets) | ✓ |
| A03 | Injection | ✓ pre-commit (padrões) | ✓ |
| A04 | Insecure Design | ✗ (inferencial) | ✓ |
| A05 | Security Misconfiguration | ✓ pre-commit (.env) | ✓ |
| A06 | Vulnerable Components | ✓ healthcheck (deps) | ✓ |
| A07 | Auth Failures | ✗ (inferencial) | ✓ |
| A08 | Software Integrity Failures | ✗ (inferencial) | ✓ |
| A09 | Logging & Monitoring Failures | ✗ (inferencial) | ✓ |
| A10 | SSRF | ✓ pre-commit (padrões) | ✓ |

---

### A01 — Broken Access Control

**Sintoma**: usuário acessa recursos de outro usuário; endpoints sem verificação de ownership; IDOR (Insecure Direct Object Reference).

**Anti-patterns**:
```
// Errado — filtra apenas no frontend
GET /api/orders/42   # retorna qualquer pedido sem checar dono

// Errado — autorização por role, não por recurso
if (user.role === 'admin') return order  // admin pode ver pedidos de outros admins?
```

**Certo**:
```
// Autorização por ownership no backend
if (order.userId !== currentUser.id) throw new ForbiddenError()

// Autorização por recurso, não por rota
const order = await orderRepo.findByIdAndUser(orderId, currentUser.id)
if (!order) throw new NotFoundError()  // não revela que existe
```

**Regra**: toda query que retorna dados de um usuário específico deve filtrar por `userId` no banco — nunca busque e filtre depois.

---

### A02 — Cryptographic Failures

**Sintoma**: dados sensíveis em texto puro; algoritmos fracos (MD5, SHA1 sem salt); secrets no código.

**Anti-patterns**:
```
// Errado — senha em MD5
password_hash = md5(password)

// Errado — secret hardcoded
const JWT_SECRET = "minha-chave-secreta-123"

// Errado — token em localStorage (acessível por XSS)
localStorage.setItem('token', jwt)
```

**Certo**:
```
// Senha com bcrypt (custo ≥ 12)
password_hash = bcrypt.hash(password, 12)

// Secret de variável de ambiente
const JWT_SECRET = process.env.JWT_SECRET  // nunca hardcode

// Token em httpOnly cookie
res.cookie('token', jwt, { httpOnly: true, secure: true, sameSite: 'strict' })
```

**Tabela de tratamento de dados sensíveis**:

| Dado | Algoritmo correto | Proibido |
|------|------------------|---------|
| Senha | bcrypt / argon2 (cost ≥ 12) | MD5, SHA1, SHA256 sem salt, texto puro |
| Token JWT | HS256 com secret ≥ 32 bytes aleatórios | secret hardcoded, HS256 com secret fraco |
| PII em repouso | AES-256-GCM | ROT13, base64, "criptografia própria" |
| API Key | gerada com CSPRNG, ≥ 32 bytes | UUID v4 (previsível), sequencial |

---

### A03 — Injection (SQL, XSS, Command, LDAP)

**Sintoma**: input do usuário concatenado em queries, templates HTML ou comandos shell.

**SQL Injection**:
```
// Errado
const users = db.query(`SELECT * FROM users WHERE email = '${email}'`)

// Certo — parameterized query
const users = db.query('SELECT * FROM users WHERE email = $1', [email])
```

**XSS (Cross-Site Scripting)**:
```
// Errado
element.innerHTML = userInput
document.write(userInput)

// Certo
element.textContent = userInput         // auto-escapes
element.innerHTML = sanitize(userInput) // DOMPurify se HTML é necessário
```

**Command Injection**:
```
// Errado
exec(`convert ${filename} output.pdf`)  // filename = "x; rm -rf /"

// Certo — nunca shell=True; use argumentos separados
execFile('convert', [filename, 'output.pdf'])
```

**Regra**: nunca concatene input externo em queries, templates ou comandos. Use sempre: parameterized queries, template engines com auto-escape, ou APIs sem shell.

---

### A04 — Insecure Design

**Sintoma**: ausência de threat modeling na spec; fluxos sem limites de tentativa; recuperação de senha por pergunta secreta.

**Detectar na fase de /spec (Three Amigos)**:
- "O que acontece se este endpoint for chamado 1000x por minuto?"
- "Um usuário pode inferir dados de outro pela resposta?"
- "O fluxo de reset de senha pode ser abusado?"

**Patterns de defesa**:
- Rate limiting agressivo em endpoints sensíveis (login, reset, OTP)
- Respostas genéricas para não revelar estado ("Email ou senha inválidos" — nunca "Email não encontrado")
- Tokens de uso único e com expiração curta para fluxos críticos
- Audit log para ações sensíveis (login, mudança de senha, deleção)

---

### A05 — Security Misconfiguration

**Sintoma**: `.env` commitado; debug mode em produção; headers de segurança ausentes; CORS aberto (`*`).

**Anti-patterns**:
```
// Errado — CORS aberto
app.use(cors({ origin: '*' }))

// Errado — debug em produção
DEBUG=true

// Errado — stack trace exposto
res.status(500).json({ error: err.stack })
```

**Certo**:
```
// CORS restrito a origens conhecidas
app.use(cors({ origin: process.env.ALLOWED_ORIGINS?.split(',') }))

// Erro genérico para o usuário, detalhe no log
res.status(500).json({ error: 'Internal server error' })
logger.error({ err, requestId }, 'Unhandled error')
```

**Headers de segurança obrigatórios**:
```
Content-Security-Policy: default-src 'self'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
```

**Regra**: `.env` sempre no `.gitignore`. Nunca exponha stack traces. CORS com lista explícita de origens.

---

### A06 — Vulnerable and Outdated Components

**Sintoma**: dependências com CVEs conhecidos; pacotes sem manutenção; versões pinadas muito antigas.

**Sensor automático**: `session-healthcheck` avisa quando `npm audit` / `pip audit` detecta vulnerabilidades críticas.

**Práticas**:
- `npm audit` / `pip audit` / `bundle audit` no CI
- Dependabot ou Renovate para atualizações automáticas
- Revisar dependências em PRs que adicionam pacotes novos
- Prefira pacotes com manutenção ativa e auditoria de segurança

---

### A07 — Identification and Authentication Failures

**Sintoma**: senhas fracas aceitas; sem MFA em áreas sensíveis; sessões que não expiram; tokens não revogáveis.

**Checklist de autenticação**:
- [ ] Senha mínima: 8+ chars, sem regras absurdas (preferir comprimento a complexidade)
- [ ] Rate limit: máximo 5 tentativas, depois lockout progressivo
- [ ] Tokens JWT: expiração curta (15min access, 7d refresh)
- [ ] Refresh tokens: revogáveis (stored server-side ou em allowlist)
- [ ] Logout: invalida token no servidor (não só no cliente)
- [ ] "Lembrar de mim": token de longa duração separado, rotacionado a cada uso

---

### A08 — Software and Data Integrity Failures

**Sintoma**: deserialização de dados não confiáveis; atualizações sem verificação de integridade; CI/CD com secrets expostos.

**Anti-patterns**:
```python
# Errado — deserialização insegura
data = pickle.loads(user_input)
config = yaml.load(user_input)         # usa Loader=SafeLoader

# Errado — sem verificação de integridade
import requests; exec(requests.get(url).text)
```

**Certo**:
```python
# Seguro
import json
data = json.loads(user_input)          # JSON é seguro

import yaml
config = yaml.safe_load(user_input)    # SafeLoader

# Verificar integridade de downloads
import hashlib
assert hashlib.sha256(content).hexdigest() == expected_hash
```

---

### A09 — Security Logging and Monitoring Failures

**Sintoma**: falhas de autenticação não logadas; sem alertas para atividade anômala; logs sem contexto suficiente.

**O que logar** (sem dados sensíveis):
```json
{
  "event": "auth.login_failed",
  "timestamp": "2026-05-06T10:30:00Z",
  "user_id": "usr_abc123",
  "ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "reason": "invalid_password",
  "attempt": 3
}
```

**Nunca logar**: senhas, tokens, números de cartão, CPF/SSN completo, dados de sessão.

**Eventos obrigatórios para audit log**:
- Login (sucesso e falha)
- Mudança de senha / email
- Alteração de permissões
- Deleção de dados
- Acesso a dados sensíveis (relatórios, exports)

---

### A10 — Server-Side Request Forgery (SSRF)

**Sintoma**: servidor faz requisição para URL fornecida pelo usuário sem validação.

**Anti-patterns**:
```
// Errado — SSRF direto
const data = await fetch(req.body.webhookUrl)

// Errado — open redirect
res.redirect(req.query.returnUrl)
```

**Certo**:
```
// Validar contra allowlist de domínios
const ALLOWED_DOMAINS = ['api.partner.com', 'hooks.slack.com']
const url = new URL(req.body.webhookUrl)
if (!ALLOWED_DOMAINS.includes(url.hostname)) throw new ForbiddenError()

// Open redirect — use identificador, não URL direta
const SAFE_REDIRECTS = { home: '/', dashboard: '/app' }
const target = SAFE_REDIRECTS[req.query.page] || '/'
res.redirect(target)
```

---

### 6.11 Secrets fora do código — regra absoluta

Secrets nunca no código, nunca em config files commitados. O pre-commit hook bloqueia automaticamente.

```
# Padrões que o hook detecta e bloqueia:
password = "valor_fixo"        → bloqueado
api_key = "sk-abc123..."       → bloqueado
JWT_SECRET = "minha-chave"     → bloqueado
AWS_SECRET_ACCESS_KEY = "..."  → bloqueado
.env (arquivo inteiro)         → bloqueado

# Correto — sempre via ambiente
SECRET = os.environ["JWT_SECRET"]
const SECRET = process.env.JWT_SECRET
```

**Secret manager para produção**: Vault, AWS Secrets Manager, GCP Secret Manager, Doppler.

---

### 6.12 Princípio do menor privilégio

Cada componente acessa apenas o que precisa:

- DB user com permissões mínimas (SELECT/INSERT apenas nas tabelas necessárias, nunca root)
- API keys com escopo limitado e expiração
- Service accounts com roles específicos
- Tokens com expiração curta; refresh tokens revogáveis

---

### 6.13 Rate limiting e proteção de endpoints

| Tipo de endpoint | Limite sugerido | Lockout |
|-----------------|----------------|---------|
| Login | 5 tentativas / 15min | 30min após 5 falhas |
| Reset de senha | 3 / hora | 24h após 3 falhas |
| OTP / MFA | 3 tentativas | invalidar token |
| API autenticada | 100-1000 / min por usuário | 429 com Retry-After |
| API pública | 10-60 / min por IP | 429 com Retry-After |

---

## 7. Harness Layers

> As três camadas de controle do SDD Kit. Cada uma combina sensores computacionais (determinísticos, rápidos) e inferenciais (LLM-based, semânticos).

| Camada | Objetivo | Sensores computacionais | Sensores inferenciais |
|--------|----------|------------------------|-----------------------|
| **Behaviour** | O sistema funciona conforme especificado | Testes BDD/TDD, approved fixtures | `/sync` (drift spec ↔ código) |
| **Maintainability** | Qualidade interna do código é sustentável | Linters, type checkers, complexity, coverage | `/review` (análise semântica de código) |
| **Architecture Fitness** | Características arquiteturais se mantêm | Testes de arquitetura, constraint validators, Fitness Functions | Revisão de ADR por LLM |

**Sensores computacionais** — determinísticos, executam em milissegundos. Configure como pre-commit hook ou CI check.

**Sensores inferenciais** — semânticos, não-determinísticos. Capturam problemas de significado que tools não enxergam (overengineering, testes redundantes, diagnóstico errado).

**Regra**: sensores computacionais correm em todo commit; inferenciais correm em PR e pós-merge.

### Sensores computacionais recomendados por camada

**Behaviour:**
- Testes unitários e de integração (test runner da stack)
- Testes E2E para fluxos críticos (Playwright, Cypress)
- Approved fixtures como âncora de regressão

**Maintainability:**
- Linter da linguagem (ESLint, pylint, golangci-lint, clippy)
- Type checker (tsc --noEmit, mypy, pyright)
- Complexidade ciclomática (cc ≤ 10 por função)
- Cobertura de testes (threshold ≥ 80%)
- Detecção de código duplicado

**Architecture Fitness:**
- Fitness Functions declaradas na PROJECT-CONSTITUTION (seção 8)
- Testes de dependências proibidas (ex: UI não importa diretamente de DB)
- Verificação de tamanho de módulo

---

## 8. Approved Fixtures

> Âncora comportamental do Behaviour Harness. Toda fixture é um "fato aprovado" que o agente não pode quebrar sem revisão humana explícita.

**O princípio**: fixtures derivadas de cenários BDD são o contrato de comportamento mais concreto do sistema. Diferente de testes (que podem ser refatorados), fixtures representam exemplos de negócio — alterar uma fixture é alterar o que o produto faz.

### Estrutura obrigatória

```json
{
  "_meta": {
    "story": "STORY-001",
    "scenario": "Login com credenciais válidas",
    "layer": "behaviour",
    "approved_by": "Jefferson",
    "approved_at": "2026-05-04"
  },
  "input": { "email": "user@test.com", "password": "valid123" },
  "expected": { "status": 200, "has_token": true }
}
```

O campo `_meta.scenario` rastreia a fixture até o cenário BDD em `specs/{story-id}/spec.bdd.md`.

### Regras

1. **Uma fixture por cenário BDD** — não crie fixtures genéricas desconectadas de spec.
2. **Mutation = aprovação** — qualquer mudança em `expected` requer nova entrada em `_meta.approved_by`.
3. **Fixtures não quebram em refactoring** — se um refactor quebra fixture, o comportamento mudou, não apenas a implementação.
4. **Dados realistas** — use valores que correspondam ao domínio real, não `foo`/`bar`/`test123`.

### Quando criar uma fixture

- Ao escrever o teste RED do cenário BDD
- Quando o input/output é complexo o suficiente para merecer arquivo separado
- Quando o mesmo exemplo precisa ser reutilizado em múltiplos testes

---

## 9. Keep Quality Left

> Distribuição temporal de sensores pelo ciclo de vida. Encontrar problemas mais cedo reduz o custo de correção.

```
Pré-commit
  └── Sensores computacionais rápidos
      ├── Linter (< 5s)
      ├── Type checker (< 10s)
      └── Testes unitários afetados (< 30s)

Commit / Push
  └── Sensores inferenciais básicos
      └── /review local pelo agente (análise de diff)

Pull Request
  ├── Revisão humana (sensor inferencial crítico)
  ├── Suite de testes completa
  └── Sensores de arquitetura (Fitness Functions)

CI/CD (pós-merge)
  ├── Suite completa + testes de integração
  ├── Mutation testing (confirma qualidade dos testes, não só cobertura)
  └── Testes E2E em ambiente staging

Contínuo (drift detection)
  ├── /sync periódico (spec ↔ código)
  ├── Cobertura de qualidade (degradação silenciosa)
  ├── Dependências desatualizadas ou vulneráveis
  └── Feedback de runtime: SLOs, anomalias em logs
```

**Por que essa ordem importa**: sensores mais baratos (computacionais, rápidos) ficam à esquerda — antes do commit. Sensores mais caros (inferenciais, mutation testing) ficam à direita — no CI, onde o custo de execução é amortizado por toda a equipe.

**Regra de ouro**: nunca mova um sensor para a direita sem justificativa. Custo de correção escala com o tempo entre o erro e sua detecção.

---

## Checklist rápido

Use durante o `/review`:

**Código**
- [ ] KISS — a solução mais simples possível?
- [ ] SOLID — cada módulo faz uma coisa?
- [ ] DRY — sem duplicação (que se repetiu 3+ vezes)?
- [ ] Nenhum anti-pattern da seção 2?

**Testes**
- [ ] Todo cenário BDD tem teste?
- [ ] Testes descrevem comportamento, não implementação?
- [ ] Fixtures com `_meta` rastreando spec?
- [ ] Fronteiras testadas?

**Error handling**
- [ ] Inputs validados no ponto de entrada?
- [ ] Erros tipados e tratáveis?
- [ ] Mensagens de erro úteis (o quê + por quê + o que fazer)?
- [ ] Logs estruturados sem dados sensíveis?

**Segurança (OWASP Top 10) — seção 6 para detalhes**
- [ ] A01: toda query filtra por userId/tenantId no banco? Sem IDOR?
- [ ] A02: nenhum secret hardcoded? Senhas com bcrypt/argon2? Tokens em httpOnly cookie?
- [ ] A03: queries parametrizadas? `innerHTML` com input do usuário? Shell sem concatenação?
- [ ] A04: rate limit em login/reset/OTP? Mensagens de erro genéricas?
- [ ] A05: `.env` no `.gitignore`? CORS restrito? Headers de segurança configurados?
- [ ] A06: novas dependências sem CVEs críticos? `npm audit` / `pip-audit` limpos?
- [ ] A07: rate limit em tentativas de login? Tokens com expiração? Logout invalida no servidor?
- [ ] A09: logs sem dados sensíveis? Falhas de auth logadas? Audit log em ações críticas?
- [ ] A10: URLs fornecidas pelo usuário validadas contra allowlist? Redirects por identificador?

**Harness**
- [ ] Toda fixture tem `_meta` rastreando o cenário BDD?
- [ ] Sensores computacionais (lint, type check, testes) passando?
- [ ] Nenhuma Fitness Function da PROJECT-CONSTITUTION violada?
- [ ] `/sync` rodado após refactor significativo?
