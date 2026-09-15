# Dia 4 - Divisão de dados e PostgreSQL

**Execução:** 01/09/2026 a 02/09/2026  
**Status:** Concluído.

## Subconjunto do MedQuAD

Com seed 42, foram selecionados exatamente 6.000 dos 16.339 registros curados. A seleção preserva grupos completos de `Focus`.

| Conjunto | Registros | Focus distintos |
|---|---:|---:|
| Treino | 4.795 | 1.384 |
| Validação | 603 | 187 |
| Teste | 602 | 183 |
| Avaliação manual | 50 | 38 |

O conjunto de avaliação é um subconjunto determinístico do teste. Ele não constitui um quinto split independente.

## Verificação de vazamento

| Comparação | Focus em comum | IDs em comum |
|---|---:|---:|
| Treino x validação | 0 | 0 |
| Treino x teste | 0 | 0 |
| Validação x teste | 0 | 0 |

Os arquivos são recriados com:

```powershell
python scripts\split_medquad.py
```

Contagens, hashes, seed e distribuição estão em `reports/evidence/dataset_split_stats.json`.

## PostgreSQL

Foram criados:

- `compose.yaml` com PostgreSQL 16 e imagem pgvector;
- migration para `patients`, `encounters`, `exams` e `pending_exams`;
- índices para consultas por paciente, data e status;
- seed com 12 pacientes, 12 atendimentos, 24 exames e 12 pendências;
- restrições que impedem `synthetic = false`;
- configuração de senha por `.env`, sem segredo versionado.

A imagem suporta pgvector, mas tabelas e embeddings vetoriais não são criados nesta etapa. Isso permanece reservado ao Dia 8.

## Validação em execução

Em 02/09/2026, a imagem foi baixada e o container `medassist-postgres` ficou saudável com PostgreSQL 16.15. As migrations foram executadas em um volume novo e produziram 12 pacientes, 12 atendimentos, 24 exames e 12 pendências. Consultas para `PAT-001` retornaram o paciente, dois exames concluídos e uma solicitação de exame agendada, todos marcados como sintéticos.
