# Histórico do projeto MedAssist

Este arquivo registra decisões, entregas e verificações relevantes. Datas de execução antecipada são preservadas para diferenciar o trabalho realizado da data planejada no cronograma.

## 31/08/2026 - Dia 1 executado antecipadamente

**Marco planejado:** 01/09/2026 - Especificação SDD e definição do MVP  
**Status:** Concluído

### Trabalho realizado

- Repositório Git inicializado na raiz do projeto.
- Estrutura modular criada para código, testes, dados, migrations, notebooks, configurações, relatórios e evidências.
- Constituição SDD criada com princípios de segurança clínica, privacidade, explicabilidade, rastreabilidade, reprodutibilidade, modularidade e controle de escopo.
- PDF oficial da Fase 3 analisado textual e visualmente; requisitos obrigatórios das páginas 2 a 4 convertidos em IDs verificáveis.
- Requisitos funcionais `RF-001` a `RF-015` e não funcionais `RNF-001` a `RNF-008` definidos com critérios de aceite.
- Casos de uso de resposta contextualizada, recusa segura, evidência insuficiente, exames pendentes, troca de provider e reprodução do fine-tuning definidos.
- Arquitetura inicial documentada com limites de componentes, modelo conceitual, fluxo LangGraph e separação entre fine-tuning e RAG.
- Decisões ADR-001 a ADR-006 registradas para MedQuAD, PostgreSQL/pgvector, Ollama, Google AI Studio, LangChain, LangGraph, LoRA/QLoRA e dados sintéticos.
- Matriz de rastreabilidade criada ligando cada obrigação do enunciado à implementação, verificação, evidência e data planejadas.
- Escopo e exclusões do MVP formalizados; nenhuma funcionalidade clínica foi indevidamente marcada como concluída.
- `.gitignore` criado para impedir versionamento de ambientes, segredos, dados brutos/processados e artefatos gerados.
- README inicial criado com o objetivo, alerta de uso acadêmico e navegação para as especificações.

### Arquivos principais

- `specs/constitution.md`
- `specs/requirements.md`
- `specs/architecture.md`
- `specs/traceability.md`
- `README.md`
- `.gitignore`

### Decisões e premissas

- O MedQuAD será usado como conteúdo médico público equivalente porque não há protocolos internos reais disponíveis.
- Apenas pacientes e exames sintéticos serão usados; nenhum dado pessoal real fará parte do projeto.
- O assistente será ferramenta acadêmica de apoio, sem prescrição, dosagem, diagnóstico definitivo ou decisão autônoma.
- Toda possível conduta exigirá validação humana e respostas sem evidência suficiente deverão se abster.
- A data de execução foi 31/08/2026, um dia antes do marco planejado, sem alteração das datas dos marcos seguintes.

### Verificações

- Todas as tarefas do Dia 1 foram conferidas na árvore do repositório.
- Todos os requisitos obrigatórios do PDF possuem identificador e evidência planejada em `specs/traceability.md`.
- A estrutura separa testes unitários, de integração e de aceite.
- O estado inicial do Git foi conferido após a criação dos artefatos.

### Próximo marco

02/09/2026 - download e análise do MedQuAD, incluindo origem, versão, licença, perfil dos XMLs, limitações e seleção preliminar de coleções.

## 01/09/2026 - Dia 2 executado antecipadamente

**Marco planejado:** 02/09/2026 - Download e análise do MedQuAD  
**Status:** Concluído

### Trabalho realizado

- Snapshot `MedQuAD-master` obtido do repositório oficial e mantido em `data/raw/`, fora do versionamento.
- Origem, licença CC BY 4.0, referência acadêmica e manifesto SHA-256 dos XMLs registrados.
- Todos os 11.274 arquivos XML das 12 coleções analisados programaticamente, sem alterar os dados brutos.
- Estatísticas por coleção, tipo de pergunta, campos ausentes, respostas vazias, esquema XML e duplicatas exportadas.
- Notebook `notebooks/01_medquad_analysis.ipynb` e relatório `reports/medquad_profile.md` produzidos.
- Nove coleções com respostas utilizáveis selecionadas preliminarmente para o MVP.
- Coleções `10_MPlus_ADAM_QA`, `11_MPlusDrugs_QA` e `12_MPlusHerbsSupplements_QA` excluídas inicialmente porque suas respostas foram removidas por copyright.

### Resultados observados

- 12 coleções e 11.274 documentos XML.
- 47.441 pares QA no snapshot local, 16 a menos que os 47.457 declarados no README da fonte.
- 16.407 pares com pergunta e resposta preenchidas.
- 31.034 respostas vazias: 31.029 nas três coleções excluídas e 5 na coleção GARD.
- 39 valores distintos de `qtype`, enquanto o README da fonte menciona 37.
- Nenhum erro de parsing XML.
- 10 documentos sem `QAPair`, 7 sem `Focus`, 4 sem `source`, 5 sem `id` e 63 sem `FocusAnnotations`.
- 2.971 grupos de perguntas normalizadas repetidas e 32 grupos de pares pergunta-resposta repetidos; a decisão de remoção ficou reservada à curadoria do Dia 3.

### Evidências

- `scripts/analyze_medquad.py`
- `notebooks/01_medquad_analysis.ipynb`
- `reports/medquad_profile.md`
- `reports/evidence/medquad_profile.json`
- `reports/evidence/medquad_collections.csv`
- `reports/evidence/medquad_question_types.csv`
- `reports/evidence/medquad_quality_issues.csv`
- `reports/evidence/medquad_schema_tags.csv`
- `reports/evidence/medquad_schema_attributes.csv`

### Próximo marco

03/09/2026 - implementar o pipeline de curadoria, normalização, identificadores estáveis, remoção de registros inválidos e geração de `medquad_curated.jsonl`.

## 01/09/2026 - Dia 3 executado antecipadamente

**Marco planejado:** 03/09/2026 - Pipeline de curadoria do MedQuAD  
**Status:** Concluído

### Trabalho realizado

- Parser determinístico implementado em `scripts/prepare_medquad.py` usando apenas a biblioteca padrão do Python.
- Unicode, entidades HTML, markup residual e espaços normalizados sem alterar deliberadamente o sentido médico.
- Metadados de pergunta, resposta, tipo, foco, sinônimos, fonte, URL, coleção, XML e UMLS preservados.
- Três coleções sem respostas por copyright excluídas.
- Registros sem campos obrigatórios e fora dos limites de tamanho removidos.
- Pares exatos duplicados eliminados após normalização.
- Identificador estável SHA-256 criado para cada registro.
- JSONL curado e estatísticas pós-curadoria gerados por comando único.
- Relatório de curadoria e seis testes unitários adicionados.

### Resultado

- 16.412 pares candidatos nas nove coleções selecionadas.
- 16.339 registros finais.
- 31.029 pares excluídos por copyright.
- 5 respostas ausentes, 1 resposta curta, 5 registros sem ID de documento, 14 sem foco e 48 duplicatas removidos.
- Hash SHA-256 da saída: `7d7db865b900c32803d082229606b743670fc29e8803f460d389c59262c7e658`.
- Tamanho da saída: 30.263.531 bytes.

### Verificações

- Seis testes unitários executados com sucesso.
- 16.339 linhas decodificadas individualmente como JSON.
- Campos obrigatórios, limites e referências à fonte validados em todas as linhas.
- IDs únicos e ausência de pares duplicados confirmados.
- Coleções excluídas confirmadas como ausentes.
- Hash físico do JSONL igual ao hash registrado nas estatísticas.

### Evidências

- `scripts/prepare_medquad.py`
- `tests/unit/test_prepare_medquad.py`
- `data/processed/medquad_curated.jsonl`
- `reports/evidence/medquad_curated_stats.json`
- `reports/medquad_curated_report.md`

### Próximo marco

04/09/2026 - selecionar o subconjunto do MVP, dividir por `Focus` sem vazamento e configurar PostgreSQL com dados sintéticos.

## 01/09/2026 a 02/09/2026 - Dia 4 executado

**Marco planejado:** 04/09/2026 - Divisão dos dados e PostgreSQL  
**Status:** Concluído

### Divisão dos dados

- 6.000 registros selecionados deterministicamente com seed 42.
- Agrupamento global por `Focus` normalizado antes da divisão.
- Treino com 4.795 registros e 1.384 focos.
- Validação com 603 registros e 187 focos.
- Teste com 602 registros e 183 focos.
- Avaliação manual com 50 registros, definida como subconjunto do teste.
- Zero focos e zero IDs sobrepostos entre treino, validação e teste.
- Arquivos e evidência reproduzíveis por `python scripts/split_medquad.py`.

### PostgreSQL e dados sintéticos

- `compose.yaml` criado com PostgreSQL 16 na imagem pgvector e healthcheck.
- Senha exigida por variável de ambiente; `.env.example` fornecido sem segredo real.
- Migration relacional criada para pacientes, atendimentos, exames e pendências.
- Seed criada com 12 pacientes, 12 atendimentos, 24 exames e 12 exames pendentes.
- Restrições SQL obrigam todos os registros das quatro tabelas a serem sintéticos.
- Instruções de inicialização e consultas por identificador registradas em `docs/database.md`.

### Verificações

- 14 testes unitários aprovados no projeto.
- Testes dos splits confirmam ausência de vazamento, determinismo e avaliação contida no teste.
- Testes estáticos confirmam tabelas, referências, restrições sintéticas, contagens da seed, imagem e mounts do Compose.
- Docker 29.7.2 e Docker Compose 5.5.0 verificados em 02/09/2026.
- Container `medassist-postgres` saudável com PostgreSQL 16.15.
- Migrations executadas em volume novo e contagens conferidas por SQL.
- `PAT-001`, seus dois exames concluídos e sua pendência agendada consultados por identificador.

### Pendência resolvida

O Docker Desktop foi instalado e validado em 02/09/2026. O banco foi iniciado por `docker compose up -d`, os dados sintéticos foram carregados e todos os critérios de aceite do Dia 4 foram atendidos.

### Evidências

- `scripts/split_medquad.py`
- `tests/unit/test_split_medquad.py`
- `tests/unit/test_database_assets.py`
- `data/processed/train.jsonl`
- `data/processed/validation.jsonl`
- `data/processed/test.jsonl`
- `data/processed/evaluation.jsonl`
- `reports/evidence/dataset_split_stats.json`
- `compose.yaml`
- `migrations/001_structured_data.sql`
- `migrations/002_seed_synthetic_data.sql`
- `docs/database.md`
- `reports/day4_data_and_database.md`

### Próximo marco

05/09/2026 - implementar a interface de providers, adapters Ollama e Google AI Studio e registrar o baseline da LLM.

## 04/09/2026 - Dia 5 em andamento: contrato, providers e seleção por ambiente

**Marco planejado:** 05/09/2026 - Baseline da LLM e providers  
**Status:** Em andamento

### Trabalho realizado

- Contrato comum `LLMProvider` criado com requisição, resposta e erros tipados.
- `OllamaProvider` implementado e validado com o modelo local `llama3.2:1b`.
- `GoogleAIProvider` implementado e validado com o modelo remoto `gemini-3.6-flash`.
- Carregamento seguro do arquivo `.env` implementado sem sobrescrever variáveis já definidas no processo.
- Factory criada para selecionar provider, modelo, endpoint e timeout por ambiente.
- A mesma função `create_llm_runtime()` alterna entre os dois adapters sem alteração nos casos de uso.
- Chave Gemini enviada somente pelo cabeçalho `x-goog-api-key` e mantida fora de URLs e mensagens de erro.

### Verificações

- Seleção padrão validada como `ollama` com `llama3.2:1b`.
- Seleção por `LLM_PROVIDER=google_ai` validada com `gemini-3.6-flash`.
- Sete testes novos para carregamento do `.env`, precedência do ambiente, providers, modelos e configurações inválidas.
- Suíte completa com 38 testes processados: 36 aprovados e duas integrações externas ignoradas por padrão.

### Evidências

- `src/medassist/infrastructure/config.py`
- `src/medassist/providers/factory.py`
- `src/medassist/providers/ollama.py`
- `src/medassist/providers/google_ai.py`
- `tests/unit/test_provider_factory.py`
- `tests/unit/test_ollama.py`
- `tests/unit/test_google_ai.py`
- `tests/integration/test_ollama_integration.py`
- `tests/integration/test_google_ai_integration.py`

## 07/09/2026 - Dia 7 concluído: fine-tuning definitivo e Ollama

**Status:** Concluído

### Resultado

- QLoRA definitivo executado com 4.795 registros de treino e 603 de validação, sem uso do teste no treinamento.
- Uma época e 600 passos concluídos em 43,38 minutos, com pico de 2,58 GB de VRAM.
- Loss de validação reduzida de 1,376935 no passo 200 para 1,321857 no passo 600.
- Adapter PEFT `1.0.0` salvo com configuração, tokenizer, métricas, logs, manifesto e hashes.
- Adapter convertido para GGUF F16 após a importação direta do Safetensors falhar ao localizar `adapter_config.json` no Ollama para Windows.
- GGUF validado com SHA-256 `4ef5939ec02b27cd2296b713e6ad2154189d108b61623a85a813ef2010e8f189`.
- Modelo `medassist-local:1.0.0` criado no Ollama, ID local `78443a2cd32f`.
- Smoke tests comprovaram carregamento do adapter, inferência em perguntas não usadas no treino, ausência de repetição degenerativa e recusa de diagnóstico e dosagem.

### Limitações registradas

- A resposta sobre cálculos renais descreveu incorretamente parte do ESWL.
- A resposta sobre neuropatia apresentou associações que exigem validação clínica.
- A resposta sobre doenças mitocondriais foi insuficiente.
- A resposta de segurança indicou `911`, inadequado como orientação fixa para usuários no Brasil.
- O modelo foi classificado como experimental; não deve ser usado clinicamente nem sem validação humana.
- Novo treinamento imediato foi adiado. RAG, curadoria, avaliação ampliada e exemplos específicos de segurança têm maior prioridade para o MVP.

### Evidências

- `notebooks/02_finetuning.ipynb`
- `reports/day7_finetuning.md`
- `reports/evidence/post_training_comparison_final.jsonl`
- `configs/ollama/Modelfile`
- `docs/ollama.md`
- `models/medassist-local/1.0.0/peft/medassist-llama32-1b-qlora-adapter-v1.0.0.zip`
- `models/medassist-local/1.0.0/ollama/medassist-llama32-1b-qlora-adapter-v1.0.0-f16.gguf`

### Próximo marco

08/09/2026 - implementar RAG com PostgreSQL e pgvector, preservando fontes e metadados para fundamentar as respostas.

## 06/09/2026 - Dia 6 concluído: fine-tuning piloto com QLoRA

**Marco planejado:** 06/09/2026 - Fine-tuning piloto  
**Status:** Concluído

### Execução

- Modelo-base: `meta-llama/Llama-3.2-1B-Instruct`.
- Técnica: QLoRA em 4 bits, com `r=8`, `lora_alpha=16` e `lora_dropout=0.05`.
- Dados: 500 registros de treino, 100 de validação e nenhum registro de teste usado no treinamento.
- Configuração: seed 42, uma época, comprimento máximo de 768 tokens, batch efetivo de 8 exemplos e 63 passos do otimizador.
- Ambiente: Kaggle com Tesla T4; execução concentrada em `cuda:0`.
- Duração do treinamento: 262,7391 segundos.
- Pico de VRAM registrado: 2,55 GB.

### Métricas e artefatos

- Loss médio de treino: 1,5962.
- Loss de validação: 1,5789 no passo 25, 1,4901 no passo 50 e 1,4866 no passo 63.
- Adapter final salvo, recarregado e usado em inferência.
- O adapter final é idêntico ao checkpoint 63, conforme verificação de hash.
- O pacote ZIP foi validado sem erros e contém adapter, tokenizer, configurações, checkpoints e logs.

### Comparação pós-treinamento

- Três perguntas reservadas do conjunto de teste foram respondidas com o modelo-base e com o adapter ativo.
- As três respostas adaptadas diferem das respostas-base, comprovando tecnicamente que o adapter foi aplicado.
- O resultado qualitativo foi misto: houve respostas mais concisas em alguns casos, mas a resposta sobre cálculos renais ficou repetitiva e menos relevante.
- O piloto comprova a viabilidade do fluxo de treinamento e inferência, mas não sustenta ainda uma alegação de melhora clínica ou de qualidade geral.
- A avaliação ampliada, os ajustes de hiperparâmetros e a investigação de exemplos problemáticos ficam para o Dia 7.

### Evidências

- `notebooks/02_finetuning.ipynb`
- `history/post_training_comparison.jsonl`

### Próximo marco

07/09/2026 - executar o fine-tuning definitivo e comparar objetivamente o modelo ajustado com o baseline.

## 04/09/2026 - Resiliência dos providers no Dia 5

- Wrapper comum `RetryingLLMProvider` implementado sem acoplamento a Ollama ou Google AI.
- Timeout e indisponibilidade classificados como falhas transitórias e repetidos de forma limitada.
- Autenticação e demais falhas não transitórias encerram imediatamente, sem nova chamada.
- Backoff exponencial configurável e latência total incluindo tentativas e esperas.
- Factory passou a aplicar a mesma política aos dois providers.
- Configurações adicionadas: `LLM_MAX_RETRIES`, `LLM_RETRY_DELAY_SECONDS` e `LLM_RETRY_BACKOFF`.
- Quatro testes específicos cobrem recuperação, esgotamento, falha não transitória e configuração inválida.
- Configuração da factory validada com os três parâmetros de retry.
- Suíte completa com 45 testes processados: 43 aprovados e duas integrações externas ignoradas por padrão.

### Evidências

- `src/medassist/application/resilience.py`
- `src/medassist/infrastructure/config.py`
- `src/medassist/providers/factory.py`
- `tests/unit/test_resilience.py`
- `tests/unit/test_provider_factory.py`
- `.env.example`

### Próxima tarefa

Executar as perguntas fixas do conjunto de avaliação nos modelos-base e registrar respostas, provider, modelo e latência.

## 04/09/2026 - Baseline dos modelos-base no Dia 5

- Pipeline reproduzível criado para ler `evaluation.jsonl`, gerar respostas e gravar cada resultado imediatamente.
- Retomada implementada para preservar sucessos, remover falhas transitórias anteriores e evitar IDs duplicados.
- 50 perguntas executadas no `llama3.2:1b` pelo Ollama: 50 sucessos e zero erros.
- 15 respostas válidas obtidas com `gemini-3.6-flash` antes do esgotamento da cota remota.
- Google AI interrompido após falhas controladas de indisponibilidade; execução pode ser retomada após renovação da cota.
- Artefatos registram pergunta, resposta de referência, resposta gerada, provider, modelo, latência, tokens, motivo de término, versão do prompt e timestamp.
- Nenhuma resposta de referência foi enviada ao modelo durante a geração.
- Verificação direta confirmou que a chave Gemini não aparece nos arquivos de baseline.
- Quatro testes unitários adicionados; suíte do projeto com 49 testes processados antes da execução real.

### Evidências

- `scripts/run_llm_baseline.py`
- `tests/unit/test_llm_baseline.py`
- `reports/evidence/baseline_ollama.jsonl`
- `reports/evidence/baseline_ollama.summary.json`
- `reports/evidence/baseline_google_ai.jsonl`
- `reports/day5_llm_baseline.md`

### Próxima tarefa

Executar a verificação final de segredos em código, configuração, testes, logs e artefatos para concluir o Dia 5.

## 04/09/2026 - Dia 5 concluído

**Marco planejado:** 05/09/2026 - Baseline da LLM e providers  
**Status:** Concluído

### Auditoria final de segredos

- Scanner reproduzível criado para comparar segredos reais do `.env` sem imprimir seus valores.
- 65 arquivos de código, testes, configuração, documentação e evidências examinados.
- Dois valores sensíveis locais comparados e nenhuma ocorrência encontrada fora do `.env`.
- Padrões de chave Google e chave privada não encontrados.
- `.env` confirmado como ignorado pelo Git.
- Nenhum arquivo de log presente no projeto.
- Testes confirmam que erros de autenticação não revelam a chave.

### Resultado consolidado

- Contrato comum, adapters Ollama e Google AI e seleção por ambiente concluídos.
- Prompt de sistema 1.0.0 criado e validado nos dois providers.
- Timeout, retry limitado, backoff e falha segura implementados.
- Baseline completo do Ollama com 50/50 sucessos.
- Baseline parcial do Google AI com 15 sucessos, retomável após renovação da cota.
- Respostas, provider, modelo, latência, tokens e versão do prompt registrados.
- Suíte final com 52 testes processados: 50 aprovados e duas integrações externas ignoradas por padrão.

### Evidências

- `src/medassist/application/llm.py`
- `src/medassist/application/prompts.py`
- `src/medassist/application/resilience.py`
- `src/medassist/providers/ollama.py`
- `src/medassist/providers/google_ai.py`
- `src/medassist/providers/factory.py`
- `scripts/run_llm_baseline.py`
- `scripts/check_secrets.py`
- `reports/day5_llm_baseline.md`
- `reports/day5_secret_audit.md`
- `reports/evidence/baseline_ollama.jsonl`
- `reports/evidence/baseline_google_ai.jsonl`

### Próximo marco

06/09/2026 - executar o fine-tuning piloto com LoRA ou QLoRA e registrar configuração, ambiente e métricas.

### Próxima tarefa

Implementar retry limitado, completar o tratamento de indisponibilidade e validar o comportamento resiliente dos dois providers.

## 04/09/2026 - Prompt de sistema inicial do Dia 5

- Prompt MedAssist `1.0.0` criado como artefato único para ambos os providers.
- Regras explícitas de evidência, abstenção, fontes, dados sintéticos, urgência, recusa de prescrição, dosagem e diagnóstico definitivo incluídas.
- Validação humana obrigatória registrada no texto do prompt.
- Três testes unitários confirmam versão, regras mínimas e ausência de placeholders de segredos.
- Smoke tests reais aprovados com `llama3.2:1b` no Ollama e `gemini-3.6-flash` no Google AI.
- Google AI configurado com `thinkingLevel=minimal` para evitar que respostas curtas consumam o limite de saída com raciocínio interno.
- Suíte final com 41 testes processados: 39 aprovados e duas integrações externas ignoradas por padrão.

### Evidências

- `src/medassist/application/prompts.py`
- `tests/unit/test_prompts.py`
- `tests/integration/test_ollama_integration.py`
- `tests/integration/test_google_ai_integration.py`
## 08/09/2026 - Dia 8 concluído: RAG com PostgreSQL e pgvector

**Status:** Concluído

### Base vetorial

- Extensão pgvector 0.8.6 habilitada no PostgreSQL 16.
- `embeddinggemma:300m` selecionado e validado como modelo multilíngue de 768 dimensões.
- 16.339 pares QA transformados em 5.479 documentos e 17.429 chunks.
- 699 pares QA extensos foram divididos, produzindo 1.090 chunks adicionais.
- Pergunta, resposta, foco, coleção, fonte, URL e metadados foram preservados.
- 17.429 embeddings persistidos, sem vetores ausentes.
- Índice HNSW criado com `m = 16`, `ef_construction = 64` e `vector_cosine_ops`; tamanho observado de 68 MB.

### Recuperação e validação

- Retriever implementado sobre Ollama, PostgreSQL e pgvector.
- Resultados incluem conteúdo, similaridade, coleção, fonte, URL e identificadores rastreáveis.
- Consultas em inglês e em português coloquial sobre cálculos renais recuperaram conteúdo relevante.
- Pergunta fora do domínio sobre Wi-Fi produziu abstenção com limiar 0,55.
- A formulação `cálculos renais` foi menos específica que `pedras nos rins`; expansão, tradução ou reranking permanecem melhorias possíveis.
- Quatro testes unitários e três testes de integração real foram aprovados.

### Evidências

- [day8_rag_pgvector.md](../reports/day8_rag_pgvector.md)
- [003_enable_vector.sql](../migrations/003_enable_vector.sql)
- [004_knowledge_base.sql](../migrations/004_knowledge_base.sql)
- [005_create_vector_index.sql](../migrations/005_create_vector_index.sql)
- [build_knowledge_chunks.py](../scripts/build_knowledge_chunks.py)
- [ingest_knowledge_base.py](../scripts/ingest_knowledge_base.py)
- [search_knowledge_base.py](../scripts/search_knowledge_base.py)
- [retrieval.py](../src/medassist/application/retrieval.py)
- [pgvector_retriever.py](../src/medassist/infrastructure/pgvector_retriever.py)
- [test_retrieval.py](../tests/unit/test_retrieval.py)
- [test_retriever_integration.py](../tests/integration/test_retriever_integration.py)

### Próximo marco

09/09/2026 - integrar o retriever ao LangChain, compor contexto estruturado e gerar respostas fundamentadas com fontes e fallback.

## 09/09/2026 - Dia 9 concluído: LangChain e resposta contextualizada

**Status:** Concluído

### Integração contextual

- Consulta estruturada e parametrizada ao PostgreSQL implementada para paciente, atendimentos, exames concluídos e exames pendentes.
- Retriever LangChain implementado como adapter sobre a recuperação pgvector validada no Dia 8.
- Contexto delimitado do paciente sintético e das evidências médicas composto antes da geração.
- Prompt de geração conectado ao provider selecionado e à resposta estruturada.
- Resposta final apresenta evidências, fontes, limitações, validação humana e proveniência.
- Fallback por insuficiência de evidências se abstém sem executar a LLM.
- Revisão de idioma configurada separadamente: gemma3:4b para Ollama e o próprio modelo configurado para Google AI.

### Validação

- Fluxo real Ollama validado com medassist-local:1.0.0, revisão em português por gemma3:4b e duas fontes NIDDK.
- Fluxo real Google AI validado com gemini-3.6-flash, resposta direta em português e duas fontes NIDDK.
- O prontuário sintético foi apresentado separadamente da evidência médica e não foi transformado em diagnóstico.
- Consulta sem evidência suficiente produziu abstenção, provider fallback e nenhuma chamada à LLM.
- Suíte final: 62 testes processados, 57 aprovados, cinco integrações externas ignoradas por padrão, zero falhas e zero erros.

### Limitações registradas

- O corpus majoritariamente em inglês pode exigir revisão adicional para perguntas em português no modelo local.
- Revisão automática de idioma pode introduzir imprecisões terminológicas e não elimina a validação humana.
- Evidência recuperada oferece informação geral e não estabelece diagnóstico para o paciente sintético.

### Evidências

- [day9_langchain_contextual_answer.md](../reports/day9_langchain_contextual_answer.md)
- [patient_context.py](../src/medassist/application/patient_context.py)
- [context_builder.py](../src/medassist/application/context_builder.py)
- [generation_prompt.py](../src/medassist/application/generation_prompt.py)
- [contextual_answer.py](../src/medassist/application/contextual_answer.py)
- [postgres_patient_repository.py](../src/medassist/infrastructure/postgres_patient_repository.py)
- [langchain_retriever.py](../src/medassist/infrastructure/langchain_retriever.py)
- [run_contextual_answer.py](../scripts/run_contextual_answer.py)
- [test_contextual_answer.py](../tests/unit/test_contextual_answer.py)
- [test_contextual_answer_language.py](../tests/unit/test_contextual_answer_language.py)

### Próximo marco

10/09/2026 - implementar a orquestração do fluxo com LangGraph.

## 10/09/2026 - Dia 10 concluído: orquestração com LangGraph

**Status:** Concluído em 12/09/2026

### Implementação

- LangGraph 1.2.11 instalado e validado no ambiente Conda `medassist`.
- Estado tipado criado para entrada, decisões, paciente, evidências, contexto, resposta, falhas e eventos de auditoria.
- Oito nós implementados e conectados em um `StateGraph` compilado.
- Dependências de paciente, recuperação e geração injetadas para permitir testes isolados.
- Auditoria em memória configurada com reducer para acumular eventos sem substituir o histórico dos nós.
- Diagrama Mermaid gerado diretamente da estrutura compilada e disponibilizado também em Markdown renderizável.

### Rotas validadas

- Entrada inválida termina em `blocked` sem acessar banco, RAG ou LLM.
- Solicitação explícita de dosagem termina em `blocked` sem acessar banco, RAG ou LLM.
- Paciente inexistente termina em `patient_not_found` sem executar RAG ou LLM.
- Ausência de evidência termina em `insufficient_context` com abstenção.
- Resposta fundamentada termina em `human_validation`.
- Indisponibilidade simulada do provider termina em `provider_error`.

### Validação

- 14 testes dos nós e seis testes do workflow aprovados.
- Suíte completa: 82 testes processados, 77 aprovados e cinco integrações externas ignoradas por padrão.
- Nenhuma falha ou erro encontrado.
- Critério mínimo de quatro caminhos superado com seis caminhos registrados.

### Evidências

- [day10_langgraph_orchestration.md](../reports/day10_langgraph_orchestration.md)
- [graph_state.py](../src/medassist/application/graph_state.py)
- [graph_nodes.py](../src/medassist/application/graph_nodes.py)
- [graph_workflow.py](../src/medassist/application/graph_workflow.py)
- [test_graph_nodes.py](../tests/unit/test_graph_nodes.py)
- [test_graph_workflow.py](../tests/unit/test_graph_workflow.py)
- [generate_graph_diagram.py](../scripts/generate_graph_diagram.py)
- [langgraph_flow.mmd](../docs/diagrams/langgraph_flow.mmd)
- [langgraph_flow.md](../docs/diagrams/langgraph_flow.md)

### Próximo marco

11/09/2026 - ampliar segurança clínica e persistir auditoria no PostgreSQL.
## 11/09/2026 - Dia 11 concluído: segurança e auditoria

**Status:** Concluído em 12/09/2026

### Segurança clínica e de entrada

- Pedidos de prescrição, dosagem individualizada, diagnóstico definitivo e
  substituição profissional são bloqueados antes do banco, RAG e LLM.
- Possíveis urgências seguem uma rota prioritária com orientação determinística.
- Tentativas básicas de prompt injection são recusadas.
- A saída estruturada da LLM é validada e todas as decisões clínicas exigem
  revisão humana.

### Auditoria e privacidade

- Migration `006_audit_events.sql` aplicada ao PostgreSQL.
- Correlation ID, timestamp, pergunta, decisão, provider, modelo, fontes,
  latência e eventos do grafo são persistidos de forma parametrizada.
- Duas execuções reais foram conferidas: uma bloqueada e outra fundamentada com
  duas fontes e rota `human_validation`.
- O contexto enviado ao Google AI remove identificadores diretos, IDs internos
  e datas exatas, preservando somente informação clínica necessária.
- Segredos em perguntas, erros e eventos são substituídos por `[REDACTED]` antes
  da auditoria; respostas completas não são armazenadas.

### Validação final

- Scanner executado sobre a estrutura oficial do projeto e valores sensíveis
  locais, sem achados; diretórios temporários permanecem fora desse escopo.
- Suíte completa: 127 testes processados, 122 aprovados e cinco integrações
  externas ignoradas por padrão; nenhuma falha ou erro.

### Evidências

- [day11_security_audit.md](../reports/day11_security_audit.md)
- [safety.py](../src/medassist/application/safety.py)
- [answer_validation.py](../src/medassist/application/answer_validation.py)
- [privacy.py](../src/medassist/application/privacy.py)
- [redaction.py](../src/medassist/application/redaction.py)
- [audit.py](../src/medassist/application/audit.py)
- [postgres_audit_repository.py](../src/medassist/infrastructure/postgres_audit_repository.py)
- [006_audit_events.sql](../migrations/006_audit_events.sql)
- [test_graph_audit.py](../tests/unit/test_graph_audit.py)
- [test_remote_context_flow.py](../tests/unit/test_remote_context_flow.py)
- [test_redaction.py](../tests/unit/test_redaction.py)

### Próximo marco

12/09/2026 - executar a avaliação comparativa e produzir evidências quantitativas e qualitativas.

## 13/09/2026 - Dia 13 — demonstrações e preparação da release candidate

**Status:** Em andamento; candidata preparada, mas ainda não congelada.

### Demonstrações locais

- Duas execuções completas foram registradas em `reports/evidence/demo/`.
- Cada execução validou quatro casos e quatro rotas esperadas.
- Não foram encontrados traceback, marcador de erro ou padrão de segredo.

### Release candidate

- Versão alvo definida como `1.0.0-rc1`.
- Checklist, configuração e gerador de manifesto adicionados.
- Manifesto gerado com 19 de 19 arquivos obrigatórios presentes e assinaturas SHA-256.
- Scanner de segredos aprovado em 158 arquivos.
- Seis testes focados nos ativos de demonstração e inicialização foram aprovados.
- A avaliação do Dia 12 foi concluída com 40 julgamentos Qwen; o congelamento aguarda a integração Google AI e os entregáveis acadêmicos finais.

### Evidências

- [day13_stabilization.md](../reports/day13_stabilization.md)
- [release_candidate.md](../docs/release_candidate.md)
- [release_candidate_manifest.json](../reports/evidence/release_candidate_manifest.json)

### Próximo marco

Concluir as pendências de avaliação e integração antes de criar commit e tag da `v1.0.0-rc1`.
## 13/09/2026 - Dia 12 concluído: avaliação comparativa final

**Status:** Concluído.

- Os 40 julgamentos qualitativos foram concluídos com `qwen2.5:7b-instruct` pelo Ollama.
- Os 32 julgamentos Gemini já obtidos foram preservados como comparação complementar.
- O cenário ajustado com RAG obteve as maiores médias qualitativas e apenas uma marcação de possível alucinação em 10 casos.
- Três SVGs finais, duas tabelas CSV e a análise final foram gerados.
- A avaliação é automática e acadêmica; não constitui revisão humana ou validação clínica.

### Evidências

- [day12_final_analysis.md](../reports/day12_final_analysis.md)
- [evaluation_final_summary.csv](../reports/evidence/evaluation_final_summary.csv)
- [evaluation_judge_agreement.csv](../reports/evidence/evaluation_judge_agreement.csv)
- [evaluation_judge_scores_final.svg](../reports/figures/evaluation_judge_scores_final.svg)
- [evaluation_groundedness_final.svg](../reports/figures/evaluation_groundedness_final.svg)
- [evaluation_hallucination_final.svg](../reports/figures/evaluation_hallucination_final.svg)
