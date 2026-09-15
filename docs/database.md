# PostgreSQL do MedAssist

O banco desta etapa contém somente dados estruturados e sintéticos de pacientes. Documentos, chunks, embeddings e índices vetoriais serão adicionados no Dia 8.

## Pré-requisitos

- Docker Desktop ou Docker Engine;
- Docker Compose v2.

## Configuração e inicialização

```powershell
Copy-Item .env.example .env
docker compose up -d
docker compose ps
docker compose exec postgres pg_isready -U medassist -d medassist
```

Altere `POSTGRES_PASSWORD` no arquivo `.env` antes de iniciar. O arquivo real é ignorado pelo Git. Na primeira criação do volume, o PostgreSQL executa `001_structured_data.sql` e `002_seed_synthetic_data.sql`.

As migrations do diretório de inicialização são executadas automaticamente somente quando o volume está vazio. Não remova um volume com dados relevantes apenas para reaplicá-las.

## Consultas de demonstração

Abra o cliente:

```powershell
docker compose exec postgres psql -U medassist -d medassist
```

Execute:

```sql
SELECT * FROM patients WHERE patient_id = 'PAT-001';

SELECT exam_id, exam_type, result_text
FROM exams
WHERE patient_id = 'PAT-001'
ORDER BY collected_at DESC;

SELECT pending_exam_id, exam_type, status
FROM pending_exams
WHERE patient_id = 'PAT-001'
  AND status IN ('pending', 'scheduled');
```

Para encerrar preservando o volume:

```powershell
docker compose down
```

## Garantias dos dados

- Os 12 pacientes e todos os eventos relacionados são fictícios.
- Identificadores usam `PAT-001`, `ENC-001`, `EXM-001` e `PEX-001`.
- Todas as tabelas exigem `synthetic = true`.
- Não há nome, CPF, telefone, endereço ou prontuário de pessoa real.
- Resultados de exames não constituem laudos nem fundamentam condutas.

## Situação da validação

Em 02/09/2026, o ambiente foi validado com Docker 29.7.2 e Docker Compose 5.5.0. O container ficou saudável com PostgreSQL 16.15, as duas migrations foram executadas e as consultas por identificador retornaram corretamente paciente, exames e pendências sintéticas.
