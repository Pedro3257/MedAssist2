# Dia 12 — Análise preliminar dos resultados

**Escopo:** métricas determinísticas das 200 execuções.  
**Estado:** preliminar; faltam oito julgamentos qualitativos do Google AI.

## Comparação entre cenários

| Comparação | Variação absoluta do F1 | Variação relativa do F1 | Variação da latência média |
|---|---:|---:|---:|
| Ajuste sem RAG versus base sem RAG | +0.137 | +267.2% | -68.1% |
| Ajuste com RAG versus base com RAG | +0.437 | +331.9% | -63.4% |
| RAG no modelo-base | +0.080 | +157.1% | +43.5% |
| RAG no modelo ajustado | +0.380 | +202.4% | +64.5% |

As comparações indicam associação entre ajuste, RAG e maior sobreposição lexical. Elas não isolam causalidade nem comprovam melhora clínica.

## Distribuição e latência

| Cenário | F1 médio | F1 mediano | F1 mínimo | F1 máximo | Latência mediana | P95 de latência |
|---|---:|---:|---:|---:|---:|---:|
| Base sem RAG | 0.051 | 0.039 | 0.005 | 0.243 | 19,703 ms | 20,296 ms |
| Ajustado sem RAG | 0.188 | 0.138 | 0.018 | 0.479 | 3,957 ms | 8,987 ms |
| Base com RAG | 0.132 | 0.093 | 0.012 | 0.577 | 20,331 ms | 49,430 ms |
| Ajustado com RAG | 0.568 | 0.536 | 0.053 | 1.000 | 6,674 ms | 13,289 ms |


## Resultados negativos observados

- O cenário base com RAG teve uma falha controlada em `medical_033`, classificada como `LLMProviderInvalidResponseError`.
- Três casos não recuperaram a URL exata de referência em nenhum dos dois cenários com RAG: `medical_012, medical_016, medical_036`.
- O modelo-base com RAG também não recuperou a URL exata em `medical_033`, justamente o caso com erro de geração.
- O melhor cenário agregado, ajustado com RAG, ainda apresentou F1 lexical mínimo de 0.053; portanto, a média de 0.568 não elimina falhas específicas.
- O P95 de latência do modelo-base com RAG chegou a 49,430 ms, acima dos demais cenários.

Os casos concretos estão em [evaluation_preliminary_negative_cases.csv](evidence/evaluation_preliminary_negative_cases.csv).

## Limitações

- F1 lexical, cobertura e ROUGE-L medem coincidência textual, não validade clínica.
- Diferenças de idioma entre resposta e referência penalizam as métricas lexicais.
- A URL exata pode falhar mesmo quando a evidência recuperada é clinicamente relacionada; essa distinção exige revisão qualitativa.
- A avaliação usa um conjunto fixo e pequeno de 40 perguntas médicas e 10 casos de segurança.
- As medições de latência refletem hardware, modelos e serviços disponíveis durante esta execução.
- Os resultados do LLM-as-a-Judge permanecem incompletos e não foram usados nesta análise.
- O julgamento automático não substitui revisão humana ou avaliação por profissional de saúde.

## Pontos para a análise final

- concluir os oito julgamentos pendentes com o mesmo provider e modelo avaliador;
- comparar relevância, correção, completude e groundedness entre os quatro cenários;
- revisar os casos marcados como possível alucinação;
- confrontar as três falhas persistentes de URL com o conteúdo efetivamente recuperado;
- registrar separadamente qualquer avaliação humana futura.
