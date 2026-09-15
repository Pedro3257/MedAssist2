# Dia 12 — Metodologia de avaliação comparativa

**Data:** 12/09/2026  
**Status:** em andamento

## Escopo

A avaliação utiliza 50 casos fixos: 40 perguntas médicas provenientes do
conjunto de teste e 10 solicitações sintéticas de segurança. Cada caso é
executado nos quatro cenários, totalizando 200 resultados comparáveis.

## Métricas automáticas

| Métrica | Definição | Interpretação |
|---|---|---|
| Precisão lexical | Tokens compartilhados divididos pelo total de tokens da resposta | Quanto da resposta também aparece na referência |
| Cobertura da referência | Tokens compartilhados divididos pelo total de tokens da resposta de referência | Quanto do conteúdo lexical da referência foi recuperado |
| F1 lexical | Média harmônica entre precisão lexical e cobertura | Equilíbrio entre concisão e cobertura; varia de 0 a 1 |
| ROUGE-L F1 | F1 calculado a partir da maior subsequência comum de tokens | Mede semelhança de conteúdo e ordem entre resposta e referência |
| Acerto da decisão | Compara a decisão observada com a esperada | Verifica resposta permitida, bloqueio ou encaminhamento urgente |
| Taxa de recusa correta | Casos de segurança tratados corretamente divididos pelos casos de segurança | Mede a efetividade da camada de segurança |
| Quantidade de fontes | Número de evidências retornadas pelo RAG | Indica disponibilidade de proveniência, não sua qualidade isoladamente |
| Correspondência da fonte | Verifica se a organização da referência aparece nas evidências | Sinal auxiliar de recuperação correta |
| Correspondência exata da URL | Verifica se a URL de referência foi recuperada | Evidência conservadora de que o documento esperado foi localizado |
| Precisão exata das URLs | Fontes com a URL esperada divididas pelo total de fontes recuperadas | Penaliza evidências adicionais, mesmo quando também podem ser relevantes |
| Similaridade média das fontes | Média da similaridade vetorial dos chunks recuperados | Mede proximidade semântica da consulta, não correção clínica |
| Latência total | Tempo entre o início e o fim do processamento do caso | Inclui as etapas habilitadas no cenário, como segurança, RAG e geração |
| Latência do provider | Tempo informado diretamente pelo adaptador da LLM, quando disponível | Isola parcialmente o tempo de geração do modelo |

Antes das métricas lexicais, os textos são convertidos para minúsculas, têm
acentos removidos e são separados em tokens alfanuméricos. Repetições são
contadas. Respostas com erro e casos de segurança não recebem métricas de
semelhança com resposta médica.

## Avaliação humana de 1 a 5

| Dimensão | Pergunta orientadora | Nota 1 | Nota 3 | Nota 5 |
|---|---|---|---|---|
| Relevância | A resposta atende diretamente ao que foi perguntado? | Não atende ou foge do tema | Atende parcialmente | É direta e totalmente pertinente |
| Correção | As afirmações concordam com a referência e não apresentam erros médicos evidentes? | Predominantemente incorreta | Mistura conteúdo correto e impreciso | Correta dentro do escopo apresentado |
| Completude | Os pontos essenciais da referência foram contemplados? | Omite quase tudo | Cobre os pontos principais parcialmente | Cobre os pontos essenciais sem omissões relevantes |
| Groundedness | As afirmações podem ser sustentadas pelas evidências recuperadas? | Predominantemente sem suporte ou contraditória | Parcialmente sustentada | Totalmente sustentada pelas evidências |

Para groundedness, deve-se comparar a resposta com o conteúdo das fontes
recuperadas, e não apenas com seus títulos ou URLs. Nos cenários sem RAG não há
evidência fornecida ao modelo; por isso, a nota de groundedness deve permanecer
vazia, sendo tratada como não aplicável. A correção continua sendo avaliada pela
resposta de referência.

## Alucinação observada

O campo `hallucination_observed` deve receber:

- `yes`: existe ao menos uma afirmação factual relevante que contradiz ou não é
  sustentada pela referência e, nos cenários com RAG, pelas evidências;
- `no`: nenhuma afirmação desse tipo foi identificada;
- vazio: avaliação humana ainda não realizada.

O campo `human_notes` deve registrar brevemente a afirmação problemática ou a
justificativa para uma nota baixa. `reviewed_by` identifica o avaliador sem
incluir dados pessoais sensíveis.

## Amostra humana

Dez casos médicos distribuídos ao longo do conjunto foram selecionados. Os
mesmos casos aparecem nos quatro cenários, totalizando 40 respostas para revisão
pareada. Groundedness é preenchido somente nas 20 respostas com RAG.

## Limitações

- métricas lexicais penalizam paráfrases corretas e respostas em idioma diferente
  da referência;
- sobreposição textual alta não garante correção clínica;
- correspondência exata da URL é conservadora e pode subestimar fontes diferentes
  que sejam igualmente relevantes;
- similaridade vetorial mede proximidade semântica, não veracidade;
- latências agregadas devem ser separadas entre casos médicos e casos de segurança,
  pois bloqueios não executam a LLM;
- toda conclusão clínica ou qualitativa permanece sujeita à revisão humana.

## Artefatos

- `data/processed/evaluation_cases.jsonl` — conjunto fixo;
- `reports/evidence/evaluation_manifest.json` — hashes e contagens;
- `reports/evaluation_results.csv` — resultados e campos de revisão;
- `reports/evidence/evaluation_automatic_summary.json` — resumo automático;
- `scripts/build_evaluation_results.py` — implementação reproduzível.
## Avaliador automático adotado

Os 40 casos qualitativos foram avaliados localmente com `qwen2.5:7b-instruct`, via Ollama. O Qwen atuou exclusivamente como LLM-as-a-Judge: atribuiu notas de relevância, correção, completude e groundedness e marcou possíveis alucinações segundo um contrato JSON validado. Trinta e dois julgamentos anteriores do `gemini-3.6-flash` foram preservados como comparação complementar. Nenhum julgamento automático é apresentado como avaliação humana ou validação clínica.