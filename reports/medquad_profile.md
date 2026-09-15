# Perfil do dataset MedQuAD

**Data da análise:** 2026-09-01  
**Origem:** https://github.com/abachaa/MedQuAD  
**Snapshot local:** `MedQuAD-master` (Download ZIP da branch `master`)  
**Manifesto SHA-256 dos XMLs:** `5584254fc7c66d2d938ccfae586fdf1f40015ba76911010183f0746b64ad9d2b`  
**Licença:** Creative Commons Attribution 4.0 International (CC BY 4.0)

## Resumo executivo

Foram analisadas 12 coleções, 11.274 arquivos XML e 47.441 pares de pergunta e resposta. Desses, 16.407 possuem pergunta e resposta preenchidas. Foram identificados 39 tipos de pergunta distintos.

O total observado é 16 pares menor que os 47.457 informados pelo autor no README. Também foram observados 39 valores distintos de `qtype`, enquanto o README menciona 37 tipos. Essas diferenças descrevem o snapshot local e serão preservadas como limitação de versionamento. As coleções `10_MPlus_ADAM_QA`, `11_MPlusDrugs_QA` e `12_MPlusHerbsSupplements_QA` não possuem respostas utilizáveis porque elas foram removidas para respeitar copyright do MedlinePlus. Essas coleções serão contabilizadas, mas excluídas do fine-tuning e do RAG do MVP.

## Perfil por coleção

| Coleção | XMLs | Pares QA | Utilizáveis | Sem resposta | Decisão preliminar | Motivo |
|---|---:|---:|---:|---:|---|---|
| `10_MPlus_ADAM_QA` | 4.366 | 17.348 | 0 | 17.348 | Excluir | respostas removidas por copyright |
| `11_MPlusDrugs_QA` | 1.312 | 12.889 | 0 | 12.889 | Excluir | respostas removidas por copyright |
| `12_MPlusHerbsSupplements_QA` | 99 | 792 | 0 | 792 | Excluir | respostas removidas por copyright |
| `1_CancerGov_QA` | 116 | 729 | 729 | 0 | Incluir | possui respostas utilizáveis |
| `2_GARD_QA` | 2.685 | 5.394 | 5.389 | 5 | Incluir | possui respostas utilizáveis |
| `3_GHR_QA` | 1.086 | 5.430 | 5.430 | 0 | Incluir | possui respostas utilizáveis |
| `4_MPlus_Health_Topics_QA` | 981 | 981 | 981 | 0 | Incluir | possui respostas utilizáveis |
| `5_NIDDK_QA` | 157 | 1.192 | 1.192 | 0 | Incluir | possui respostas utilizáveis |
| `6_NINDS_QA` | 277 | 1.088 | 1.088 | 0 | Incluir | possui respostas utilizáveis |
| `7_SeniorHealth_QA` | 48 | 769 | 769 | 0 | Incluir | possui respostas utilizáveis |
| `8_NHLBI_QA_XML` | 88 | 559 | 559 | 0 | Incluir | possui respostas utilizáveis |
| `9_CDC_QA` | 59 | 270 | 270 | 0 | Incluir | possui respostas utilizáveis |

## Qualidade e estrutura

| Ocorrência | Quantidade |
|---|---:|
| `document_without_qapairs` | 10 |
| `empty_answer` | 31.034 |
| `missing_document_id` | 5 |
| `missing_focus` | 7 |
| `missing_source` | 4 |

- Erros de parsing XML: **0**.
- Grupos de perguntas normalizadas repetidas: **2971** (6963 registros envolvidos).
- Grupos de pares pergunta-resposta exatamente repetidos após normalização: **32** (80 registros envolvidos).
- Grupos de `qid` repetidos: **9662** (27017 registros envolvidos).
- Documentos sem CUI: **3547**; com ao menos um CUI: **7727**.

As duplicatas aqui são apenas sinalizadas. A remoção e a definição de identificadores estáveis pertencem ao pipeline de curadoria do Dia 3.

## Seleção preliminar para o MVP

### Incluir

- `1_CancerGov_QA`
- `2_GARD_QA`
- `3_GHR_QA`
- `4_MPlus_Health_Topics_QA`
- `5_NIDDK_QA`
- `6_NINDS_QA`
- `7_SeniorHealth_QA`
- `8_NHLBI_QA_XML`
- `9_CDC_QA`

### Excluir inicialmente

- `10_MPlus_ADAM_QA`
- `11_MPlusDrugs_QA`
- `12_MPlusHerbsSupplements_QA`

Não será feita recaptura das respostas removidas. A seleção de 3.000 a 8.000 pares e a divisão por `Focus` serão realizadas no Dia 4, depois da curadoria.

## Idioma, cobertura e limitações

- O conteúdo é predominantemente em inglês; o dataset não oferece cobertura nativa sistemática em português.
- A cobertura inclui doenças, medicamentos, suplementos, exames e outros tópicos de saúde provenientes de 12 fontes/coleções de sites NIH e MedlinePlus.
- As respostas variam muito de tamanho e algumas contêm listas longas ou texto concatenado da página de origem.
- A presença e a granularidade de anotações UMLS variam entre coleções.
- O dataset é informativo e não representa protocolos internos de um hospital brasileiro.
- A idade do conteúdo e a disponibilidade atual das URLs não foram validadas clinicamente nesta etapa.
- O texto não deve ser tratado como prescrição ou diagnóstico e qualquer possível conduta requer validação humana.
- A licença exige atribuição; o projeto deve citar o dataset e o artigo de Ben Abacha e Demner-Fushman (2019).
- Cinco pares da coleção `2_GARD_QA` também possuem respostas vazias e deverão ser removidos na curadoria.
- Dez documentos não contêm nenhum `QAPair`; eles permanecem no inventário, mas não geram exemplos de treinamento.

## Evidências reproduzíveis

- `reports/evidence/medquad_profile.json`: perfil completo e manifesto.
- `reports/evidence/medquad_collections.csv`: estatísticas por coleção.
- `reports/evidence/medquad_question_types.csv`: tipos de pergunta por coleção.
- `reports/evidence/medquad_quality_issues.csv`: amostras limitadas de problemas encontrados.
- `reports/evidence/medquad_schema_tags.csv`: tags observadas por coleção.
- `reports/evidence/medquad_schema_attributes.csv`: atributos observados por coleção.
- `notebooks/01_medquad_analysis.ipynb`: roteiro reproduzível da análise.

## Referência obrigatória

Asma Ben Abacha e Dina Demner-Fushman. *A Question-Entailment Approach to Question Answering*. BMC Bioinformatics, 20, 511 (2019). https://doi.org/10.1186/s12859-019-3119-4
