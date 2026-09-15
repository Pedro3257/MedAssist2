# Fine-tuning definitivo e integração com Ollama

**Data de execução:** 07/09/2026  
**Modelo-base:** `meta-llama/Llama-3.2-1B-Instruct`  
**Modelo local:** `medassist-local:1.0.0`

## Treinamento

- Técnica: QLoRA em 4 bits com NF4 e double quantization.
- LoRA: rank 8, alpha 16, dropout 0,05 e adapters nas projeções de atenção e MLP.
- Treino: 4.795 registros.
- Validação: 603 registros.
- Teste usado no treinamento: zero registros.
- Seed: 42.
- Épocas: 1.
- Comprimento máximo: 1.024 tokens.
- Batch efetivo: 8.
- Passos do otimizador: 600.
- Tempo: 43,38 minutos.
- Pico de VRAM: 2,58 GB em Tesla T4.

## Métricas

| Passo | Training loss | Validation loss | Mean token accuracy |
|---:|---:|---:|---:|
| 200 | 1,322608 | 1,376935 | 0,678247 |
| 400 | 1,260524 | 1,332324 | 0,685335 |
| 600 | 1,356919 | 1,321857 | 0,687311 |

- Loss médio de treino: 1,357977.
- Melhor checkpoint: 600.
- A redução contínua da loss de validação confirma aprendizado durante a época, mas não comprova precisão clínica.

## Artefatos e hashes

- Pacote PEFT `medassist-llama32-1b-qlora-adapter-v1.0.0.zip`: `116fb47389f0e0742375753755f94b338d9fcfa8ba7aad93fc8e9c265996bac0`.
- Adapter PEFT `adapter_model.safetensors`: `3c83779aa25c6fd6f882f96e9c7ec6bd2ee1572e7590831645ed5f78d9a9e4e6`.
- Adapter GGUF F16: `4ef5939ec02b27cd2296b713e6ad2154189d108b61623a85a813ef2010e8f189`.
- Modelo Ollama: `medassist-local:1.0.0`, ID local `78443a2cd32f`.

## Inferência e smoke tests

- Três perguntas do teste, ausentes do treinamento, foram comparadas entre o modelo-base e o adapter definitivo.
- O modelo local respondeu a perguntas sobre cálculos renais, neuropatia de fibras pequenas e doenças mitocondriais.
- O teste de segurança recusou diagnóstico definitivo, medicamento e dosagem.
- O adapter registrado pelo Ollama possui o mesmo hash do GGUF validado.
- Não ocorreu repetição degenerativa nos smoke tests locais.

## Avaliação qualitativa

- A resposta sobre cálculos renais ficou coerente e incluiu ESWL, ureteroscopia e nefrolitotomia percutânea, mas descreveu incorretamente parte do procedimento ESWL.
- A resposta sobre neuropatia incluiu associações e sintomas que exigem validação clínica.
- A resposta sobre doenças mitocondriais foi curta e não respondeu adequadamente ao tratamento.
- A recusa de diagnóstico e dosagem funcionou, mas indicou `911`; a orientação regional de emergência deve ser corrigida para usar serviço local, incluindo SAMU 192 no Brasil.

O resultado demonstra fine-tuning, conversão e inferência local reais. Não demonstra segurança ou eficácia clínica. Um novo treinamento imediato não foi recomendado: RAG, curadoria, avaliação ampliada e exemplos de segurança têm maior prioridade para o MVP.

## Evidências

- `notebooks/02_finetuning.ipynb`
- `reports/evidence/post_training_comparison_final.jsonl`
- `models/medassist-local/1.0.0/peft/medassist-llama32-1b-qlora-adapter-v1.0.0.zip`
- `models/medassist-local/1.0.0/peft/medassist-llama32-1b-qlora-adapter-v1.0.0.zip.sha256.txt`
- `models/medassist-local/1.0.0/ollama/medassist-llama32-1b-qlora-adapter-v1.0.0-f16.gguf`
- `models/medassist-local/1.0.0/ollama/medassist-llama32-1b-qlora-adapter-v1.0.0-f16.gguf.sha256.txt`
- `configs/ollama/Modelfile`
- `docs/ollama.md`
