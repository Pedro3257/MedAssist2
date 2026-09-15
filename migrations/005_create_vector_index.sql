-- Cria o índice vetorial HNSW para acelerar a recuperação
-- semântica dos chunks usando distância por cosseno.

BEGIN;

CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_embedding_hnsw
    ON knowledge_chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (
        m = 16,
        ef_construction = 64
    );

ANALYZE knowledge_chunks;

COMMIT;