-- Executado automaticamente na primeira subida do container.
CREATE EXTENSION IF NOT EXISTS vector;

-- Deputados (API /deputados). O id é o mesmo do campo ideCadastro do arquivo de cotas.
CREATE TABLE IF NOT EXISTS deputados (
    id          INTEGER PRIMARY KEY,
    nome        TEXT NOT NULL,
    partido     TEXT,
    uf          CHAR(2),
    legislatura INTEGER,
    url_foto    TEXT
);

-- Despesas da Cota para o Exercício da Atividade Parlamentar (CEAP).
-- Fonte: arquivos anuais Ano-{ano}.csv.zip. Conferir nomes de colunas no arquivo real.
CREATE TABLE IF NOT EXISTS despesas (
    id             BIGSERIAL PRIMARY KEY,
    id_documento   BIGINT,
    deputado_id    INTEGER REFERENCES deputados(id), -- nulo em despesas de lideranças
    nome_parlamentar TEXT NOT NULL,   -- nome do deputado ou da liderança
    partido        TEXT,              -- partido na época da despesa
    uf             TEXT,              -- UF na época da despesa
    ano            SMALLINT NOT NULL,
    mes            SMALLINT NOT NULL,
    categoria      TEXT NOT NULL,     -- ex.: passagens aéreas, combustíveis
    subcategoria   TEXT,              -- especificação da categoria, quando houver
    fornecedor     TEXT,
    cnpj_fornecedor TEXT,             -- só CNPJ; CPF de pessoa física não é armazenado (LGPD)
    data_emissao   DATE,
    valor_documento NUMERIC(12,2),
    valor_glosa    NUMERIC(12,2),
    valor_liquido  NUMERIC(12,2) NOT NULL,
    url_documento  TEXT
);

CREATE INDEX IF NOT EXISTS idx_despesas_deputado ON despesas (deputado_id);
CREATE INDEX IF NOT EXISTS idx_despesas_periodo  ON despesas (ano, mes);
CREATE INDEX IF NOT EXISTS idx_despesas_categoria ON despesas (categoria);
CREATE INDEX IF NOT EXISTS idx_despesas_uf ON despesas (uf);

-- Normas e documentos sobre a CEAP, para o RAG (o que pode e o que não pode ser reembolsado).
CREATE TABLE IF NOT EXISTS documentos (
    id        BIGSERIAL PRIMARY KEY,
    fonte     TEXT NOT NULL,          -- nome e link da norma
    trecho    TEXT NOT NULL,
    embedding vector(384)             -- deve bater com EMBEDDING_DIM
);

CREATE INDEX IF NOT EXISTS idx_documentos_embedding
    ON documentos USING hnsw (embedding vector_cosine_ops);

-- Usuário somente leitura para o agente: mesmo que o LLM gere um comando destrutivo,
-- o banco recusa. É a segunda camada de proteção (a primeira é o sql_guard).
CREATE ROLE agente_leitura LOGIN PASSWORD 'leitura';
GRANT CONNECT ON DATABASE camara TO agente_leitura;
GRANT USAGE ON SCHEMA public TO agente_leitura;
GRANT SELECT ON deputados, despesas TO agente_leitura;
ALTER ROLE agente_leitura SET statement_timeout = '5s';
