# Baseline dos modelos de linguagem

**Data de execução:** 04/09/2026  
**Prompt de sistema:** 1.0.0  
**Conjunto:** `data/processed/evaluation.jsonl`

## Configuração

- 50 perguntas fixas do subconjunto de avaliação do MedQuAD.
- A resposta de referência não foi enviada ao modelo; foi preservada somente no artefato para comparação posterior.
- Temperatura 0,1 e limite de 256 tokens de saída.
- Resultados gravados incrementalmente em JSONL.
- Timeout e retry limitado aplicados pela factory comum.

## Ollama

- Provider: `ollama`.
- Modelo-base: `llama3.2:1b`.
- 50 respostas concluídas em 50 perguntas, sem erro.
- 50 IDs únicos.
- Latência média: 12.251,510 ms.
- Latência mínima: 2.984,668 ms.
- Latência máxima: 15.571,451 ms.
- Tokens de entrada: 21.208.
- Tokens de saída: 10.626.

## Google AI

- Provider: `google_ai`.
- Modelo-base: `gemini-3.6-flash`.
- 15 respostas concluídas.
- 7 tentativas registradas como indisponibilidade após esgotamento da cota.
- Latência média dos sucessos: 9.216,397 ms.
- Tokens de entrada dos sucessos: 5.181.
- Tokens de saída dos sucessos: 2.934.
- Execução interrompida de forma controlada para evitar consumo inútil; o comando com `--resume` permite continuar após a renovação da cota.

## Retomada do Google AI

```powershell
$env:PYTHONPATH = 'src'
python scripts/run_llm_baseline.py --provider google_ai --max-tokens 256 --delay-seconds 5 --resume --output reports/evidence/baseline_google_ai.jsonl
```

Na retomada, sucessos anteriores são preservados, erros são removidos e somente IDs ainda não concluídos são enviados novamente.

## Segurança e limitações

- Somente perguntas públicas do MedQuAD foram enviadas aos providers.
- Nenhum dado real de paciente foi utilizado.
- A chave Gemini não aparece nos artefatos inspecionados.
- Estes resultados são um baseline técnico e não demonstram desempenho clínico.
- Avaliação de qualidade, segurança e similaridade com a referência será realizada em etapa posterior.

## Evidências

- `reports/evidence/baseline_ollama.jsonl`
- `reports/evidence/baseline_ollama.summary.json`
- `reports/evidence/baseline_google_ai.jsonl`
- `scripts/run_llm_baseline.py`
