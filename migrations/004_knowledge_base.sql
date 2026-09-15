-- Cria as tabelas que armazenam os documentos, chunks, metadados
-- e embeddings utilizados pelo RAG do MedAssist.

BEGIN;

CREATE TABLE IF NOT EXISTS knowledge_documents (
    document_id bigserial PRIMARY KEY,
    external_id varchar(255) NOT NULL UNIQUE,
    collection varchar(100) NOT NULL,
    source varchar(100),
    title text NOT NULL,
    url text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id bigserial PRIMARY KEY,
    document_id bigint NOT NULL
        REFERENCES knowledge_documents(document_id)
        ON DELETE CASCADE,
    external_id varchar(255) NOT NULL UNIQUE,
    chunk_index integer NOT NULL,
    content text NOT NULL,
    question text,
    answer text,
    token_count integer,
    embedding_model varchar(100) NOT NULL
        DEFAULT 'embeddinggemma:300m',
    embedding vector(768),
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_knowledge_chunks_document_index
        UNIQUE (document_id, chunk_index),

    CONSTRAINT ck_knowledge_chunks_index
        CHECK (chunk_index >= 0),

    CONSTRAINT ck_knowledge_chunks_content
        CHECK (length(btrim(content)) > 0),

    CONSTRAINT ck_knowledge_chunks_token_count
        CHECK (token_count IS NULL OR token_count > 0)
);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_collection
    ON knowledge_documents(collection);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_source
    ON knowledge_documents(source);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document
    ON knowledge_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_documents_metadata
    ON knowledge_documents USING gin(metadata);

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_metadata
    ON knowledge_chunks USING gin(metadata);

COMMENT ON TABLE knowledge_documents IS
    'Documentos médicos que formam a base de conhecimento do RAG.';

COMMENT ON TABLE knowledge_chunks IS
    'Trechos dos documentos com embeddings para recuperação semântica.';

COMMENT ON COLUMN knowledge_chunks.embedding IS
    'Embedding de 768 dimensões gerado pelo embeddinggemma:300m.';

COMMIT;