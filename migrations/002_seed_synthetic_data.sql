BEGIN;

-- Todos os registros abaixo sao integralmente ficticios e existem apenas
-- para demonstracao academica. Nao foram derivados de pessoas reais.
INSERT INTO patients
    (patient_id, display_name, birth_date, biological_sex, synthetic)
VALUES
    ('PAT-001', 'Paciente Sintetico 001', '1980-05-14', 'female', true),
    ('PAT-002', 'Paciente Sintetico 002', '1972-11-03', 'male', true),
    ('PAT-003', 'Paciente Sintetico 003', '1991-02-22', 'female', true),
    ('PAT-004', 'Paciente Sintetico 004', '1965-07-09', 'male', true),
    ('PAT-005', 'Paciente Sintetico 005', '2000-01-18', 'female', true),
    ('PAT-006', 'Paciente Sintetico 006', '1987-09-30', 'male', true),
    ('PAT-007', 'Paciente Sintetico 007', '1958-04-11', 'female', true),
    ('PAT-008', 'Paciente Sintetico 008', '1995-12-06', 'male', true),
    ('PAT-009', 'Paciente Sintetico 009', '1978-03-25', 'female', true),
    ('PAT-010', 'Paciente Sintetico 010', '1983-08-17', 'male', true),
    ('PAT-011', 'Paciente Sintetico 011', '2002-06-02', 'female', true),
    ('PAT-012', 'Paciente Sintetico 012', '1969-10-28', 'not_informed', true);

INSERT INTO encounters
    (encounter_id, patient_id, occurred_at, reason, clinical_notes, synthetic)
VALUES
    ('ENC-001', 'PAT-001', '2026-08-20 09:00:00-03', 'Fadiga persistente', 'Relato ficticio de cansaco ha duas semanas.', true),
    ('ENC-002', 'PAT-002', '2026-08-20 10:00:00-03', 'Acompanhamento metabolico', 'Consulta ficticia para revisao de exames de rotina.', true),
    ('ENC-003', 'PAT-003', '2026-08-21 08:30:00-03', 'Cefaleia recorrente', 'Cenario sintetico sem sinais de alarme registrados.', true),
    ('ENC-004', 'PAT-004', '2026-08-21 11:00:00-03', 'Acompanhamento cardiovascular', 'Registro ficticio de retorno ambulatorial.', true),
    ('ENC-005', 'PAT-005', '2026-08-22 09:15:00-03', 'Desconforto abdominal', 'Sintomas ficticios leves e intermitentes.', true),
    ('ENC-006', 'PAT-006', '2026-08-22 14:00:00-03', 'Tosse persistente', 'Cenario academico com tosse sem avaliacao diagnostica.', true),
    ('ENC-007', 'PAT-007', '2026-08-23 10:30:00-03', 'Dor articular', 'Registro sintetico para consulta de exames inflamatorios.', true),
    ('ENC-008', 'PAT-008', '2026-08-24 13:00:00-03', 'Acompanhamento preventivo', 'Consulta preventiva inteiramente ficticia.', true),
    ('ENC-009', 'PAT-009', '2026-08-25 08:00:00-03', 'Palpitacoes ocasionais', 'Cenario ficticio encaminhado para avaliacao profissional.', true),
    ('ENC-010', 'PAT-010', '2026-08-25 15:00:00-03', 'Alteracao do sono', 'Relato sintetico de sono fragmentado.', true),
    ('ENC-011', 'PAT-011', '2026-08-26 09:45:00-03', 'Alergia sazonal', 'Cenario ficticio de sintomas sazonais.', true),
    ('ENC-012', 'PAT-012', '2026-08-27 11:30:00-03', 'Revisao de exames', 'Consulta sintetica para demonstrar contexto longitudinal.', true);

INSERT INTO exams
    (exam_id, patient_id, encounter_id, exam_type, collected_at, result_text, reference_text, synthetic)
VALUES
    ('EXM-001', 'PAT-001', 'ENC-001', 'Hemograma', '2026-08-20 09:30:00-03', 'Hemoglobina 11,2 g/dL', 'Exemplo ficticio; interpretar apenas em demonstracao.', true),
    ('EXM-002', 'PAT-001', 'ENC-001', 'TSH', '2026-08-20 09:30:00-03', 'TSH 2,1 mUI/L', 'Exemplo ficticio; nao constitui laudo.', true),
    ('EXM-003', 'PAT-002', 'ENC-002', 'Glicemia', '2026-08-20 10:30:00-03', 'Glicemia 108 mg/dL', 'Valor sintetico.', true),
    ('EXM-004', 'PAT-002', 'ENC-002', 'Hemoglobina glicada', '2026-08-20 10:30:00-03', 'HbA1c 5,9 por cento', 'Valor sintetico.', true),
    ('EXM-005', 'PAT-003', 'ENC-003', 'Hemograma', '2026-08-21 09:00:00-03', 'Sem alteracoes no cenario ficticio', 'Texto sintetico.', true),
    ('EXM-006', 'PAT-003', 'ENC-003', 'Proteina C reativa', '2026-08-21 09:00:00-03', 'PCR 1,2 mg/L', 'Valor sintetico.', true),
    ('EXM-007', 'PAT-004', 'ENC-004', 'Colesterol total', '2026-08-21 11:30:00-03', 'Colesterol total 210 mg/dL', 'Valor sintetico.', true),
    ('EXM-008', 'PAT-004', 'ENC-004', 'Creatinina', '2026-08-21 11:30:00-03', 'Creatinina 1,0 mg/dL', 'Valor sintetico.', true),
    ('EXM-009', 'PAT-005', 'ENC-005', 'Hemograma', '2026-08-22 09:45:00-03', 'Sem alteracoes no cenario ficticio', 'Texto sintetico.', true),
    ('EXM-010', 'PAT-005', 'ENC-005', 'ALT', '2026-08-22 09:45:00-03', 'ALT 24 U/L', 'Valor sintetico.', true),
    ('EXM-011', 'PAT-006', 'ENC-006', 'Oximetria', '2026-08-22 14:30:00-03', 'Saturacao 97 por cento', 'Valor sintetico.', true),
    ('EXM-012', 'PAT-006', 'ENC-006', 'Hemograma', '2026-08-22 14:30:00-03', 'Sem alteracoes no cenario ficticio', 'Texto sintetico.', true),
    ('EXM-013', 'PAT-007', 'ENC-007', 'Proteina C reativa', '2026-08-23 11:00:00-03', 'PCR 4,0 mg/L', 'Valor sintetico.', true),
    ('EXM-014', 'PAT-007', 'ENC-007', 'Acido urico', '2026-08-23 11:00:00-03', 'Acido urico 5,1 mg/dL', 'Valor sintetico.', true),
    ('EXM-015', 'PAT-008', 'ENC-008', 'Hemograma', '2026-08-24 13:30:00-03', 'Sem alteracoes no cenario ficticio', 'Texto sintetico.', true),
    ('EXM-016', 'PAT-008', 'ENC-008', 'Glicemia', '2026-08-24 13:30:00-03', 'Glicemia 89 mg/dL', 'Valor sintetico.', true),
    ('EXM-017', 'PAT-009', 'ENC-009', 'TSH', '2026-08-25 08:30:00-03', 'TSH 3,0 mUI/L', 'Valor sintetico.', true),
    ('EXM-018', 'PAT-009', 'ENC-009', 'Potassio', '2026-08-25 08:30:00-03', 'Potassio 4,2 mmol/L', 'Valor sintetico.', true),
    ('EXM-019', 'PAT-010', 'ENC-010', 'Ferritina', '2026-08-25 15:30:00-03', 'Ferritina 80 ng/mL', 'Valor sintetico.', true),
    ('EXM-020', 'PAT-010', 'ENC-010', 'Vitamina B12', '2026-08-25 15:30:00-03', 'Vitamina B12 410 pg/mL', 'Valor sintetico.', true),
    ('EXM-021', 'PAT-011', 'ENC-011', 'Hemograma', '2026-08-26 10:15:00-03', 'Eosinofilos 5 por cento', 'Valor sintetico.', true),
    ('EXM-022', 'PAT-011', 'ENC-011', 'IgE total', '2026-08-26 10:15:00-03', 'IgE 120 UI/mL', 'Valor sintetico.', true),
    ('EXM-023', 'PAT-012', 'ENC-012', 'Creatinina', '2026-08-27 12:00:00-03', 'Creatinina 1,1 mg/dL', 'Valor sintetico.', true),
    ('EXM-024', 'PAT-012', 'ENC-012', 'Hemograma', '2026-08-27 12:00:00-03', 'Hemoglobina 13,5 g/dL', 'Valor sintetico.', true);

INSERT INTO pending_exams
    (pending_exam_id, patient_id, encounter_id, exam_type, requested_at, scheduled_for, status, synthetic)
VALUES
    ('PEX-001', 'PAT-001', 'ENC-001', 'Ferritina', '2026-08-20 09:00:00-03', '2026-09-03 08:00:00-03', 'scheduled', true),
    ('PEX-002', 'PAT-002', 'ENC-002', 'Perfil lipidico', '2026-08-20 10:00:00-03', NULL, 'pending', true),
    ('PEX-003', 'PAT-003', 'ENC-003', 'Avaliacao oftalmologica', '2026-08-21 08:30:00-03', NULL, 'pending', true),
    ('PEX-004', 'PAT-004', 'ENC-004', 'Eletrocardiograma', '2026-08-21 11:00:00-03', '2026-09-04 10:00:00-03', 'scheduled', true),
    ('PEX-005', 'PAT-005', 'ENC-005', 'Ultrassonografia abdominal', '2026-08-22 09:15:00-03', NULL, 'pending', true),
    ('PEX-006', 'PAT-006', 'ENC-006', 'Radiografia de torax', '2026-08-22 14:00:00-03', '2026-09-02 14:00:00-03', 'scheduled', true),
    ('PEX-007', 'PAT-007', 'ENC-007', 'Fator reumatoide', '2026-08-23 10:30:00-03', NULL, 'pending', true),
    ('PEX-008', 'PAT-008', 'ENC-008', 'Perfil lipidico', '2026-08-24 13:00:00-03', NULL, 'pending', true),
    ('PEX-009', 'PAT-009', 'ENC-009', 'Holter', '2026-08-25 08:00:00-03', '2026-09-05 09:00:00-03', 'scheduled', true),
    ('PEX-010', 'PAT-010', 'ENC-010', 'Polissonografia', '2026-08-25 15:00:00-03', NULL, 'pending', true),
    ('PEX-011', 'PAT-011', 'ENC-011', 'Teste cutaneo alergico', '2026-08-26 09:45:00-03', NULL, 'pending', true),
    ('PEX-012', 'PAT-012', 'ENC-012', 'Taxa de filtracao glomerular', '2026-08-27 11:30:00-03', '2026-09-06 08:30:00-03', 'scheduled', true);

COMMIT;
