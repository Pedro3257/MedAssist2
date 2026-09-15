BEGIN;

CREATE TABLE patients (
    patient_id varchar(16) PRIMARY KEY,
    display_name varchar(100) NOT NULL,
    birth_date date NOT NULL,
    biological_sex varchar(20) NOT NULL
        CHECK (biological_sex IN ('female', 'male', 'intersex', 'not_informed')),
    synthetic boolean NOT NULL DEFAULT true CHECK (synthetic),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (patient_id ~ '^PAT-[0-9]{3}$')
);

CREATE TABLE encounters (
    encounter_id varchar(16) PRIMARY KEY,
    patient_id varchar(16) NOT NULL
        REFERENCES patients(patient_id) ON DELETE RESTRICT,
    occurred_at timestamptz NOT NULL,
    reason varchar(200) NOT NULL,
    clinical_notes text NOT NULL,
    synthetic boolean NOT NULL DEFAULT true CHECK (synthetic),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (encounter_id ~ '^ENC-[0-9]{3}$')
);

CREATE TABLE exams (
    exam_id varchar(16) PRIMARY KEY,
    patient_id varchar(16) NOT NULL
        REFERENCES patients(patient_id) ON DELETE RESTRICT,
    encounter_id varchar(16)
        REFERENCES encounters(encounter_id) ON DELETE SET NULL,
    exam_type varchar(120) NOT NULL,
    collected_at timestamptz NOT NULL,
    result_text text NOT NULL,
    reference_text text,
    status varchar(20) NOT NULL DEFAULT 'completed'
        CHECK (status = 'completed'),
    synthetic boolean NOT NULL DEFAULT true CHECK (synthetic),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (exam_id ~ '^EXM-[0-9]{3}$')
);

CREATE TABLE pending_exams (
    pending_exam_id varchar(16) PRIMARY KEY,
    patient_id varchar(16) NOT NULL
        REFERENCES patients(patient_id) ON DELETE RESTRICT,
    encounter_id varchar(16)
        REFERENCES encounters(encounter_id) ON DELETE SET NULL,
    exam_type varchar(120) NOT NULL,
    requested_at timestamptz NOT NULL,
    scheduled_for timestamptz,
    status varchar(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'scheduled', 'cancelled')),
    synthetic boolean NOT NULL DEFAULT true CHECK (synthetic),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (pending_exam_id ~ '^PEX-[0-9]{3}$')
);

CREATE INDEX idx_encounters_patient_occurred
    ON encounters (patient_id, occurred_at DESC);
CREATE INDEX idx_exams_patient_collected
    ON exams (patient_id, collected_at DESC);
CREATE INDEX idx_pending_exams_patient_status
    ON pending_exams (patient_id, status);

COMMENT ON TABLE patients IS
    'Exclusivamente pacientes ficticios para demonstracao academica.';
COMMENT ON TABLE encounters IS
    'Atendimentos integralmente sinteticos, sem origem em prontuarios reais.';
COMMENT ON TABLE exams IS
    'Resultados ficticios; nao utilizar para decisao clinica.';
COMMENT ON TABLE pending_exams IS
    'Solicitacoes ficticias usadas apenas para testar o fluxo do assistente.';

COMMIT;
