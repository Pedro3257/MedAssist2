-- Habilita a extensão pgvector no banco do MedAssist.
-- IF NOT EXISTS torna a migration segura para reaplicação.

BEGIN;

CREATE EXTENSION IF NOT EXISTS vector;

COMMENT ON EXTENSION vector IS
    'Extensao vetorial usada pelo RAG do MedAssist.';

COMMIT;