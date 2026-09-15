-- Cria a tabela de auditoria das execuções do MedAssist.
-- Cada linha representa o resultado final de uma execução do grafo.

BEGIN;

CREATE TABLE IF NOT EXISTS audit_events (
    audit_event_id bigserial PRIMARY KEY,

    correlation_id uuid NOT NULL UNIQUE,

    patient_id varchar(16),

    question text NOT NULL,

    decision varchar(40) NOT NULL
        CHECK (
            decision IN (
                'blocked',
                'urgent',
                'patient_not_found',
                'insufficient_context',
                'human_validation',
                'provider_error',
                'completed'
            )
        ),

    provider varchar(50),

    model varchar(150),

    sources jsonb NOT NULL DEFAULT '[]'::jsonb,

    latency_ms numeric(12, 3),

    requires_human_validation boolean NOT NULL
        DEFAULT true,

    error_code varchar(100),

    graph_events jsonb NOT NULL DEFAULT '[]'::jsonb,

    synthetic boolean NOT NULL DEFAULT true
        CHECK (synthetic),

    created_at timestamptz NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_audit_events_question
        CHECK (length(btrim(question)) > 0),

    CONSTRAINT ck_audit_events_patient_id
        CHECK (
            patient_id IS NULL
            OR patient_id ~ '^PAT-[0-9]{3}$'
        ),

    CONSTRAINT ck_audit_events_latency
        CHECK (
            latency_ms IS NULL
            OR latency_ms >= 0
        ),

    CONSTRAINT ck_audit_events_sources_json
        CHECK (
            jsonb_typeof(sources) = 'array'
        ),

    CONSTRAINT ck_audit_events_graph_events_json
        CHECK (
            jsonb_typeof(graph_events) = 'array'
        )
);

CREATE INDEX IF NOT EXISTS idx_audit_events_created_at
    ON audit_events (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_events_decision
    ON audit_events (decision);

CREATE INDEX IF NOT EXISTS idx_audit_events_patient
    ON audit_events (patient_id)
    WHERE patient_id IS NOT NULL;

COMMENT ON TABLE audit_events IS
    'Auditoria de execucoes do MedAssist com dados exclusivamente sinteticos.';

COMMENT ON COLUMN audit_events.question IS
    'Pergunta associada exclusivamente a um paciente sintetico de demonstracao.';

COMMENT ON COLUMN audit_events.sources IS
    'Fontes publicas recuperadas pelo RAG, armazenadas como array JSON.';

COMMENT ON COLUMN audit_events.graph_events IS
    'Decisoes internas dos nos do LangGraph sem segredos ou respostas completas.';

COMMIT;