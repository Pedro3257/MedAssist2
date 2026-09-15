# Relatório de curadoria do MedQuAD

**Execução:** 01/09/2026  
**Entrada:** `data/raw/MedQuAD-master`  
**Saída:** `data/processed/medquad_curated.jsonl`  
**SHA-256 da saída:** `7d7db865b900c32803d082229606b743670fc29e8803f460d389c59262c7e658`

## Resultado

O pipeline percorreu 11.274 XMLs das 12 coleções. As três coleções cujas respostas foram removidas por copyright foram contabilizadas e excluídas antes da curadoria. Dos 16.412 pares candidatos restantes, 16.339 registros válidos e únicos foram gravados no JSONL.

| Resultado | Registros |
|---|---:|
| Pares nas coleções excluídas por copyright | 31.029 |
| Pares candidatos à curadoria | 16.412 |
| Registros curados | 16.339 |
| Respostas ausentes | 5 |
| Respostas abaixo do mínimo | 1 |
| Documento sem identificador | 5 |
| Foco ausente | 14 |
| Duplicatas exatas removidas | 48 |

Os motivos de rejeição são mutuamente exclusivos: cada registro é associado à primeira regra não atendida.

## Registros por coleção

| Coleção | Registros curados |
|---|---:|
| `1_CancerGov_QA` | 729 |
| `2_GARD_QA` | 5.389 |
| `3_GHR_QA` | 5.430 |
| `4_MPlus_Health_Topics_QA` | 981 |
| `5_NIDDK_QA` | 1.144 |
| `6_NINDS_QA` | 1.088 |
| `7_SeniorHealth_QA` | 769 |
| `8_NHLBI_QA_XML` | 559 |
| `9_CDC_QA` | 250 |

## Regras aplicadas

- Unicode normalizado em NFC.
- Entidades HTML decodificadas e markup residual removido.
- Espaços, tabulações e quebras de linha consecutivos convertidos em um espaço.
- Perguntas aceitas entre 10 e 500 caracteres.
- Respostas aceitas entre 20 e 30.000 caracteres.
- Campos obrigatórios: IDs de documento e pergunta, tipo, foco, pergunta, resposta, fonte, URL, coleção e caminho do XML.
- Duplicata exata definida pela pergunta e resposta normalizadas, sem distinguir maiúsculas de minúsculas.
- Primeiro registro na ordem determinística de coleção e caminho é preservado.
- Identificador estável derivado de coleção, XML, IDs, pergunta e resposta normalizadas por SHA-256.

## Esquema do JSONL

Cada linha contém:

- `id`;
- `document_id`, `question_id` e `pair_id`;
- `question`, `answer` e `question_type`;
- `focus` e `focus_synonyms`;
- `source`, `url`, `collection` e `xml_path`;
- `umls_cuis`, `semantic_types` e `semantic_groups`.

Listas UMLS podem permanecer vazias porque essas anotações não existem em todos os documentos. Fonte, URL, coleção e caminho do XML são obrigatórios para garantir rastreabilidade.

## Reprodutibilidade

Comando único:

```powershell
python scripts\prepare_medquad.py
```

O comando recria o dataset e `reports/evidence/medquad_curated_stats.json`. A gravação do JSONL é atômica, evitando que uma falha deixe uma saída parcial.

## Verificações executadas

- seis testes unitários aprovados;
- todas as 16.339 linhas decodificadas como JSON;
- presença dos campos obrigatórios conferida;
- IDs verificados como únicos;
- ausência de pares duplicados confirmada;
- limites de tamanho conferidos;
- coleções de copyright confirmadas como ausentes;
- hash do arquivo confirmado contra a evidência;
- 30.263.531 bytes na saída final.

## Limitações

- A normalização é estrutural e não altera ou valida o sentido médico.
- Não há tradução do conteúdo em inglês.
- Não há atualização clínica das respostas ou validação das URLs nesta etapa.
- A seleção do subconjunto de 3.000 a 8.000 pares e os splits por `Focus` pertencem ao Dia 4.
