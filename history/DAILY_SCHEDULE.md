# MedAssist - Cronograma diário de implementação

## Informações do projeto

- **Projeto:** Tech Challenge FIAP - Fase 3
- **Período de execução:** 01/09/2026 a 15/09/2026
- **Data limite:** 15/09/2026
- **Dataset principal:** MedQuAD
- **Banco de dados:** PostgreSQL com pgvector
- **Providers de LLM:** Ollama e Google AI Studio
- **Metodologia:** Specification-Driven Development (SDD)

## Objetivo do MVP

Entregar um assistente médico acadêmico capaz de:

- responder perguntas médicas com base em um subconjunto curado do MedQuAD;
- consultar pacientes, atendimentos e exames sintéticos no PostgreSQL;
- recuperar conhecimento médico por RAG usando PostgreSQL e pgvector;
- utilizar uma LLM local por Ollama ou uma LLM remota pelo Google AI Studio;
- apresentar evidência de fine-tuning com LoRA ou QLoRA;
- citar as fontes utilizadas nas respostas;
- recusar prescrições, dosagens e diagnósticos definitivos;
- encaminhar decisões clínicas para validação humana;
- registrar logs de auditoria;
- coordenar o fluxo do assistente com LangChain e LangGraph;
- comparar o modelo-base, o modelo ajustado e o uso de RAG.

## Escopo congelado

### Incluído no MVP

- curadoria de um subconjunto do MedQuAD;
- dados sintéticos de pacientes e exames;
- PostgreSQL para dados relacionais e auditoria;
- pgvector para documentos, chunks e embeddings;
- pipeline de fine-tuning reproduzível;
- providers Ollama e Google AI Studio;
- RAG com fontes e metadados;
- fluxo LangGraph;
- segurança em camadas;
- avaliação técnica e humana simplificada;
- README, relatório, diagramas e vídeo demonstrativo.

### Fora do MVP

- classificador de risco de sepse;
- dados reais de pacientes;
- interface web sofisticada;
- autenticação hospitalar real;
- microsserviços;
- implantação em nuvem;
- tradução integral do MedQuAD;
- treinamento de uma LLM do zero;
- automação de qualquer conduta clínica real.

### Backlog de melhorias pós-MVP

- criar versões separadas em português brasileiro de train.jsonl, validation.jsonl e test.jsonl, preservando os arquivos originais em inglês;
- manter cada tradução no mesmo split do registro original para impedir vazamento entre treino, validação e teste;
- registrar idioma, identificador do registro original, método, modelo e versão utilizados na tradução;
- revisar uma amostra estratificada das traduções, com atenção à terminologia médica e à preservação do significado clínico;
- executar um experimento de fine-tuning em português ou bilíngue sem substituir o treinamento em inglês do MVP;
- criar um conjunto de avaliação específico em português e comparar o modelo-base, o modelo ajustado em inglês e o modelo ajustado ou bilíngue;
- documentar qualidade, custos, limitações e riscos introduzidos pela tradução automática.
- ampliar a avaliação clínica e factual antes de considerar novo fine-tuning;
- revisar e limpar respostas problemáticas do MedQuAD antes de novas épocas de treinamento;
- incluir exemplos específicos de abstenção, segurança e orientação regional de emergência;
- comparar modelos maiores e novas configurações de LoRA/QLoRA de forma controlada;
- corrigir a orientação de emergência para utilizar o serviço local, incluindo SAMU 192 no Brasil;
- avaliar o quanto o RAG reduz respostas incompletas ou sem sustentação nas fontes recuperadas.

## Arquitetura resumida

```text
Usuário / API
     |
     v
LangGraph Orchestrator
     |
     +-- Safety Check
     +-- Consulta ao paciente e exames
     +-- Recuperação RAG
     +-- Geração pela LLM
     +-- Validação da resposta
     +-- Auditoria
            |
            v
PostgreSQL + pgvector
     +-- patients
     +-- encounters
     +-- exams
     +-- pending_exams
     +-- knowledge_documents
     +-- knowledge_chunks
     +-- audit_events

Providers de LLM
     +-- Ollama
     +-- Google AI Studio
```

O fine-tuning e o RAG são pipelines distintos:

```text
MedQuAD curado -> JSONL instrucional -> LoRA/QLoRA -> modelo customizado

MedQuAD curado -> documentos/chunks -> embeddings -> pgvector -> RAG
```

## Critério geral de conclusão

Uma funcionalidade somente poderá ser considerada concluída quando possuir:

1. requisito ou especificação correspondente;
2. implementação reproduzível;
3. teste ou demonstração executada;
4. evidência registrada;
5. documentação mínima.

---

## 01/09/2026 - Especificação SDD e definição do MVP

**Status:** Concluído antecipadamente em 31/08/2026.

### Objetivo

Definir o que será entregue e evitar crescimento descontrolado do escopo.

### Tarefas

- [x] iniciar o repositório Git;
- [x] criar a estrutura de diretórios do projeto;
- [x] criar `specs/constitution.md`;
- [x] criar `specs/requirements.md`;
- [x] criar `specs/architecture.md`;
- [x] criar `specs/traceability.md`;
- [x] converter os requisitos do PDF em requisitos identificáveis;
- [x] definir casos de uso e critérios de aceite;
- [x] registrar as decisões de usar MedQuAD, PostgreSQL, pgvector, Ollama e Google AI Studio;
- [x] documentar explicitamente o escopo e as exclusões do MVP.

### Entregáveis

- estrutura inicial do repositório;
- especificação inicial;
- matriz de rastreabilidade.

### Critério de aceite

- todos os requisitos obrigatórios do desafio possuem identificador e evidência planejada.

**Resultado:** Atendido. A matriz `specs/traceability.md` cobre todas as obrigações identificadas nas páginas 2 a 4 do PDF oficial, com IDs, implementação, verificação e data de evidência planejadas.

---

## 02/09/2026 - Download e análise do MedQuAD

**Status:** Concluído antecipadamente em 01/09/2026.

### Objetivo

Compreender a estrutura, a qualidade e as limitações do dataset.

### Tarefas

- [x] baixar o repositório oficial do MedQuAD;
- [x] registrar origem, versão e licença;
- [x] inspecionar os arquivos XML;
- [x] contar perguntas por coleção e tipo;
- [x] identificar registros sem resposta;
- [x] identificar campos ausentes e duplicatas;
- [x] excluir inicialmente as coleções cujas respostas foram removidas por copyright;
- [x] documentar idioma, cobertura temática e limitações;
- [x] selecionar preliminarmente as coleções que entrarão no MVP.

### Entregáveis

- `notebooks/01_medquad_analysis.ipynb`;
- relatório de perfil do dataset.

### Critério de aceite

- quantidades, campos, coleções, licença e critérios de exclusão documentados.

**Resultado:** Atendido. Foram analisados 11.274 XMLs de 12 coleções, sem erro de parsing. O snapshot contém 47.441 pares QA, dos quais 16.407 têm pergunta e resposta preenchidas. Nove coleções foram selecionadas preliminarmente; três foram excluídas porque suas respostas foram removidas por copyright. O perfil completo e as evidências estão em `reports/medquad_profile.md` e `reports/evidence/`.

---

## 03/09/2026 - Pipeline de curadoria do MedQuAD

**Status:** Concluído antecipadamente em 01/09/2026.

### Objetivo

Converter o MedQuAD em um formato limpo, rastreável e reproduzível.

### Tarefas

- [x] implementar o parser dos XMLs;
- [x] normalizar espaços, HTML e caracteres;
- [x] preservar pergunta, resposta, tipo, foco, fonte, URL, coleção e UMLS CUI;
- [x] eliminar registros sem resposta;
- [x] eliminar duplicatas exatas;
- [x] validar tamanhos mínimos e máximos;
- [x] adicionar identificador estável a cada registro;
- [x] gerar `medquad_curated.jsonl`;
- [x] gerar estatísticas depois da curadoria.

### Entregáveis

- `scripts/prepare_medquad.py`;
- dataset curado;
- testes do parser e das validações.

### Critério de aceite

- o dataset curado pode ser recriado com um único comando;
- todos os registros mantêm referência à fonte.

**Resultado:** Atendido. O comando `python scripts/prepare_medquad.py` gerou 16.339 registros válidos em `data/processed/medquad_curated.jsonl`. Todas as linhas mantêm fonte, URL, coleção e XML de origem. Seis testes unitários e a validação integral do JSONL foram aprovados; estatísticas e hash estão em `reports/evidence/medquad_curated_stats.json`.

---

## 04/09/2026 - Divisão dos dados e PostgreSQL

**Status:** Concluído em 02/09/2026.

### Objetivo

Preparar os conjuntos de treinamento e avaliação e a persistência dos dados estruturados.

### Tarefas

- [x] selecionar entre 3.000 e 8.000 pares para o MVP;
- [x] separar treino, validação e teste por doença ou foco;
- [x] impedir vazamento da mesma entidade entre treino e teste;
- [x] criar um conjunto reduzido para avaliação manual;
- [x] configurar PostgreSQL por Docker Compose;
- [x] criar migrations iniciais;
- [x] criar tabelas para pacientes, atendimentos, exames e exames pendentes;
- [x] criar entre 10 e 20 pacientes sintéticos;
- [x] carregar os dados sintéticos no PostgreSQL;
- [x] documentar que não são utilizados dados pessoais reais.

### Entregáveis

- `train.jsonl`;
- `validation.jsonl`;
- `test.jsonl`;
- `evaluation.jsonl`;
- `compose.yaml`;
- migrations e dados sintéticos.

### Critério de aceite

- PostgreSQL pode ser iniciado com um comando;
- não existe sobreposição indevida entre treino e teste;
- pacientes e exames podem ser consultados por identificador.

**Resultado:** Atendido. Foram selecionados 6.000 registros e gerados treino (4.795), validação (603), teste (602) e avaliação manual (50), com zero `Focus` ou IDs sobrepostos entre os três splits. O PostgreSQL 16.15 iniciou saudável por Docker Compose, executou as migrations e carregou 12 pacientes, 12 atendimentos, 24 exames e 12 pendências sintéticas. Paciente e exames foram consultados por identificador.

---

## 05/09/2026 - Baseline da LLM e providers

**Status:** Concluído em 04/09/2026.

### Objetivo

Obter geração funcional antes do fine-tuning e criar uma interface independente de provider.

### Tarefas

- [x] definir a interface `LLMProvider`;
- [x] implementar `OllamaProvider`;
- [x] implementar `GoogleAIProvider`;
- [x] selecionar o provider por variável de ambiente;
- [x] criar o prompt de sistema inicial;
- [x] implementar timeout, retry e tratamento de indisponibilidade;
- [x] executar perguntas do conjunto de avaliação no modelo-base;
- [x] armazenar respostas, provider, modelo e latência;
- [x] impedir o registro de chaves de API.

### Entregáveis

- dois adapters de LLM;
- configuração por ambiente;
- resultados de baseline.

### Critério de aceite

- a aplicação alterna entre Ollama e Google AI Studio sem alteração nos casos de uso.

**Resultado:** Atendido. O mesmo contrato e a mesma factory alternam entre Ollama e Google AI por configuração. O baseline completo do Ollama registrou 50 respostas sem erro; o Google AI foi validado e produziu 15 respostas antes do limite de cota. Timeout, retry, prompt seguro, métricas e auditoria de segredos foram implementados. A suíte final processou 52 testes, com 50 aprovados e duas integrações externas ignoradas por padrão.

### Contingência

- se a API remota atrasar o desenvolvimento, manter o adapter e priorizar Ollama na demonstração principal.

---

## 06/09/2026 - Fine-tuning piloto

**Status:** Concluído em 06/09/2026.

### Objetivo

Executar uma primeira prova real de fine-tuning.

### Tarefas

- [x] converter os pares para formato instrucional;
- [x] selecionar uma LLM aberta pequena compatível com o hardware disponível;
- [x] configurar LoRA ou QLoRA;
- [x] executar um treinamento piloto com 500 a 1.000 exemplos;
- [x] registrar modelo-base, seed, hiperparâmetros e ambiente;
- [x] monitorar memória, tempo e loss;
- [x] salvar o adapter LoRA;
- [x] executar perguntas simples com o modelo ajustado.

### Entregáveis

- `notebooks/02_finetuning.ipynb` ou script equivalente;
- configuração de treinamento;
- adapter piloto;
- logs do treinamento.

### Critério de aceite

- o treinamento foi realmente executado;
- o adapter pode ser carregado e utilizado em uma inferência.

**Resultado:** Critério atendido. O piloto QLoRA do `meta-llama/Llama-3.2-1B-Instruct` treinou 500 exemplos por uma época (63 passos), salvou o adapter e o recarregou para inferência em três perguntas reservadas do teste. As respostas adaptadas diferiram das respostas do modelo-base, confirmando o uso do adapter. A comparação qualitativa foi mista e não demonstra ainda melhora clínica geral; essa limitação deverá orientar os ajustes do Dia 7.

**Evidências:** `notebooks/02_finetuning.ipynb` e `history/post_training_comparison.jsonl`.

---

## 07/09/2026 - Fine-tuning definitivo e Ollama

**Status:** Concluído em 07/09/2026.

### Objetivo

Produzir a versão demonstrável do modelo customizado.

### Tarefas

- [x] corrigir os problemas encontrados no piloto;
- [x] executar o fine-tuning com o subconjunto final;
- [x] salvar adapter, configuração e métricas;
- [x] preparar ou converter o modelo para inferência local;
- [x] integrar o modelo customizado ao Ollama;
- [x] registrar versão e hash dos artefatos;
- [x] executar smoke tests;
- [x] comparar respostas preliminares do modelo-base e do modelo ajustado.

### Entregáveis

- modelo ou adapter final;
- modelo `medassist-local` disponível para inferência;
- instruções de reprodução.

### Critério de aceite

- existe evidência reproduzível de fine-tuning;
- o modelo ajustado responde a perguntas não usadas no treino.

### Contingência

- se a conversão para Ollama falhar, demonstrar o adapter com Transformers/PEFT e usar o modelo-base do Ollama no fluxo, documentando claramente a diferença.

**Resultado:** Critério atendido. O treinamento definitivo processou 4.795 registros em 600 passos, alcançou `eval_loss` 1,321857 e gerou um adapter PEFT versionado. Após uma limitação da importação Safetensors no Ollama para Windows, o adapter foi convertido para GGUF F16 e registrado como `medassist-local:1.0.0`. Perguntas não usadas no treino e um cenário de segurança foram executados localmente. A integração técnica foi aprovada, mas a avaliação qualitativa encontrou imprecisões médicas e respostas incompletas; o modelo permanece experimental e exige RAG e validação humana.

**Evidências:** `notebooks/02_finetuning.ipynb`, `reports/day7_finetuning.md`, `reports/evidence/post_training_comparison_final.jsonl`, `configs/ollama/Modelfile` e `docs/ollama.md`.

---

## 08/09/2026 - RAG com PostgreSQL e pgvector

### Objetivo

Construir a base de conhecimento vetorial do assistente.

### Tarefas

- [x] habilitar a extensão pgvector;
- [x] escolher e registrar um modelo multilíngue de embeddings;
- [x] definir a dimensão dos vetores;
- [x] criar tabelas `knowledge_documents` e `knowledge_chunks`;
- [x] converter registros do MedQuAD em documentos e chunks;
- [x] preservar pergunta e resposta no mesmo contexto quando apropriado;
- [x] gerar embeddings;
- [x] carregar embeddings, conteúdo e metadados no PostgreSQL;
- [x] criar índice vetorial adequado ao volume do MVP;
- [x] implementar busca por similaridade;
- [x] testar perguntas em inglês e português.

### Entregáveis

- migrations do pgvector;
- pipeline de ingestão;
- base vetorial persistente;
- testes do retriever.

### Critério de aceite

- cada resultado recuperado possui conteúdo, similaridade, coleção, fonte e URL;
- uma pergunta sem evidência suficiente pode produzir abstenção.

**Resultado:** Critério atendido. O PostgreSQL foi preparado com pgvector 0.8.6, e o modelo multilíngue `embeddinggemma:300m` foi validado com vetores de 768 dimensões. Os 16.339 pares QA do MedQuAD foram organizados em 5.479 documentos e 17.429 chunks, todos vetorizados e persistidos sem embeddings ausentes. Um índice HNSW com distância por cosseno foi criado. O retriever recuperou corretamente conteúdos sobre cálculos renais em inglês e em português coloquial, retornando similaridade, coleção, fonte e URL, e se absteve diante de uma pergunta sobre configuração de Wi-Fi com o limiar inicial de 0,55. Quatro testes unitários e três testes de integração foram aprovados.

**Evidências:** [003_enable_vector.sql](../migrations/003_enable_vector.sql), [004_knowledge_base.sql](../migrations/004_knowledge_base.sql), [005_create_vector_index.sql](../migrations/005_create_vector_index.sql), [build_knowledge_chunks.py](../scripts/build_knowledge_chunks.py), [ingest_knowledge_base.py](../scripts/ingest_knowledge_base.py), [search_knowledge_base.py](../scripts/search_knowledge_base.py), [retrieval.py](../src/medassist/application/retrieval.py), [pgvector_retriever.py](../src/medassist/infrastructure/pgvector_retriever.py), [test_retrieval.py](../tests/unit/test_retrieval.py), [test_retriever_integration.py](../tests/integration/test_retriever_integration.py) e [day8_rag_pgvector.md](../reports/day8_rag_pgvector.md).

---

## 09/09/2026 - LangChain e resposta contextualizada

### Objetivo

Integrar paciente, exames, RAG, prompt e LLM.

### Tarefas

- [x] implementar consulta estruturada ao PostgreSQL;
- [x] implementar retriever LangChain sobre pgvector;
- [x] compor o contexto do paciente e dos exames pendentes;
- [x] criar o prompt de geração;
- [x] conectar prompt, provider e parser da resposta;
- [x] definir resposta estruturada;
- [x] incluir fontes e limitações;
- [x] implementar fallback para falta de evidência;
- [x] testar com Ollama e Google AI Studio.

### Entregáveis

- [x] pipeline LangChain funcional;
- [x] testes de integração.

### Critério de aceite

- [x] o prompt é efetivamente executado;
- [x] a resposta utiliza dados do paciente correto;
- [x] as fontes recuperadas são apresentadas ao usuário.

**Resultado:** Atendido. O pipeline integra o paciente sintético PAT-001, exames, recuperação pgvector, prompt LangChain e geração selecionável por provider. Ollama e Google AI Studio foram validados em execuções reais; respostas apresentam evidências, fontes, limitações e validação humana. A ausência de evidência aciona abstenção sem chamada à LLM. A suíte final processou 62 testes, com 57 aprovados, cinco integrações externas ignoradas por padrão e nenhuma falha.

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

---

## 10/09/2026 - Orquestração com LangGraph

### Objetivo

Implementar o fluxo automatizado solicitado pelo desafio.

### Tarefas

- [x] definir o estado tipado do grafo;
- [x] implementar nós de validação, segurança, paciente, exames, RAG, geração, validação e auditoria;
- [x] implementar rota para solicitação bloqueada;
- [x] implementar rota para paciente inexistente;
- [x] implementar rota para contexto insuficiente;
- [x] implementar rota que exige validação humana;
- [x] implementar tratamento de falha do provider;
- [x] gerar o diagrama do fluxo.

### Entregáveis

- [x] grafo compilado;
- [x] testes das rotas;
- [x] diagrama Mermaid ou equivalente.

### Critério de aceite

- [x] pelo menos quatro caminhos diferentes do grafo são executados e registrados.

**Resultado:** Atendido. O `StateGraph` compilado contém oito nós e coordena validação, segurança, paciente e exames, RAG, contexto, geração, validação humana e auditoria. Seis caminhos foram exercitados: entrada inválida, solicitação bloqueada, paciente inexistente, contexto insuficiente, resposta fundamentada com validação humana e falha do provider. A suíte completa processou 82 testes, com 77 aprovados, cinco integrações externas ignoradas por padrão e nenhuma falha.

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

---

## 11/09/2026 - Segurança e auditoria

### Objetivo

Adicionar limites clínicos e rastreabilidade ao assistente.

### Tarefas

- [x] bloquear prescrição, dosagem e diagnóstico definitivo;
- [x] detectar pedidos para substituir avaliação profissional;
- [x] tratar possíveis situações de urgência;
- [x] adicionar validação humana obrigatória;
- [x] implementar proteção básica contra prompt injection;
- [x] validar a saída estruturada da LLM;
- [x] criar a tabela `audit_events`;
- [x] registrar correlation ID, timestamp, pergunta, decisão, provider, modelo, fontes e latência;
- [x] minimizar dados de paciente enviados ao provider remoto;
- [x] garantir que logs não contenham segredos.

### Entregáveis

- [x] módulo de segurança;
- [x] persistência de auditoria no PostgreSQL;
- [x] suíte de testes de segurança.

### Critério de aceite

- [x] casos proibidos são recusados;
- [x] as decisões podem ser rastreadas no PostgreSQL;
- [x] nenhuma chave de API aparece nos logs.

**Resultado:** Atendido. Controles clínicos, urgência, prompt injection, validação estruturada, revisão humana, minimização remota e auditoria persistente foram integrados ao LangGraph. Duas rotas reais foram rastreadas no PostgreSQL. O scanner final verificou a estrutura oficial sem encontrar segredos, e a suíte processou 127 testes: 122 aprovados, cinco integrações externas ignoradas por padrão e nenhuma falha.

### Evidências

- [day11_security_audit.md](../reports/day11_security_audit.md)
- [safety.py](../src/medassist/application/safety.py)
- [answer_validation.py](../src/medassist/application/answer_validation.py)
- [privacy.py](../src/medassist/application/privacy.py)
- [redaction.py](../src/medassist/application/redaction.py)
- [audit.py](../src/medassist/application/audit.py)
- [postgres_audit_repository.py](../src/medassist/infrastructure/postgres_audit_repository.py)
- [006_audit_events.sql](../migrations/006_audit_events.sql)
- [run_medassist_graph.py](../scripts/run_medassist_graph.py)
- [test_remote_context_flow.py](../tests/unit/test_remote_context_flow.py)
- [test_redaction.py](../tests/unit/test_redaction.py)
---

## 12/09/2026 - Avaliação comparativa

### Objetivo

Produzir evidências quantitativas e qualitativas para o relatório.

### Cenários

- modelo-base sem RAG;
- modelo-base com RAG;
- modelo ajustado sem RAG;
- modelo ajustado com RAG.

### Tarefas

- [x] executar entre 30 e 50 casos fixos;
- [x] incluir ao menos 10 casos de segurança;
- [x] registrar respostas brutas e fontes;
- [x] concluir a avaliação automática de relevância, correção, completude e groundedness — 40 de 40 julgamentos concluídos pelo `qwen2.5:7b-instruct`; 32 julgamentos Gemini preservados para comparação complementar;
- [x] avaliar precisão das referências;
- [x] medir taxa de recusa correta;
- [x] concluir o registro automático de alucinações observadas — 40 de 40 casos qualitativos registrados;
- [x] medir latência por provider;
- [x] manter a avaliação humana simplificada de 1 a 5 como validação opcional; para o MVP, foi adotado LLM-as-a-Judge em campos separados, sem apresentá-lo como avaliação humana;
- [x] produzir tabelas e gráficos preliminares com as métricas determinísticas completas;
- [x] concluir a análise final de resultados negativos e limitações — métricas determinísticas, 40 julgamentos Qwen e comparação parcial com 32 julgamentos Gemini incorporados.

### Decisão registrada em 13/09/2026

- preservar os 32 julgamentos do provider `google_ai` como verificação complementar;
- usar 40 julgamentos do `qwen2.5:7b-instruct` como conjunto qualitativo principal, sem classificá-los como avaliação humana ou clínica.

### Metodologia

- [day12_evaluation_methodology.md](../reports/day12_evaluation_methodology.md)

### Entregáveis

- [evaluation_results.csv](../reports/evaluation_results.csv);
- [evaluation_preliminary_summary.csv](../reports/evidence/evaluation_preliminary_summary.csv);
- [resultados preliminares](../reports/day12_preliminary_results.md);
- [análise preliminar de resultados e limitações](../reports/day12_preliminary_analysis.md);
- [casos negativos preliminares](../reports/evidence/evaluation_preliminary_negative_cases.csv);
- [gráfico de qualidade lexical](../reports/figures/evaluation_quality_preliminary.svg);
- [gráfico de latência](../reports/figures/evaluation_latency_preliminary.svg);
- [gráfico de recuperação de referências](../reports/figures/evaluation_reference_retrieval_preliminary.svg);
- [resumo qualitativo final](../reports/evidence/evaluation_final_summary.csv);
- [concordância Qwen–Gemini](../reports/evidence/evaluation_judge_agreement.csv);
- [análise comparativa final](../reports/day12_final_analysis.md);
- [gráfico final de notas qualitativas](../reports/figures/evaluation_judge_scores_final.svg);
- [gráfico final de groundedness](../reports/figures/evaluation_groundedness_final.svg);
- [gráfico final de alucinações](../reports/figures/evaluation_hallucination_final.svg).

### Critério de aceite

- os resultados podem ser reproduzidos com o mesmo conjunto de avaliação;
- as conclusões são fundamentadas nos resultados observados.

---

## 13/09/2026 - Testes e estabilização

### Objetivo

Congelar uma versão estável para demonstração.

### Tarefas

- [x] executar testes unitários — 146 testes aprovados;
- [x] executar testes de integração — quatro integrações locais e integração remota final com Google AI aprovadas;
- [x] testar migrations em um banco vazio — migrations `001` a `006` aprovadas em banco temporário isolado;
- [x] testar a recriação da base vetorial — teste isolado aprovado com 10 chunks, embeddings 768D e índice HNSW;
- [x] verificar caminhos relativos e configuração — 108 links válidos, Docker Compose válido e nenhum caminho local proibido nos artefatos oficiais;
- [x] revisar `.env.example` — variáveis de banco, providers, embeddings, resiliência e integrações documentadas sem segredos;
- [x] congelar dependências — dependências locais, treinamento Kaggle e lock transitivo registrados;
- [x] criar comando único de inicialização — PostgreSQL, dependências, Ollama, modelos e base vetorial validados;
- [x] preparar roteiro e perguntas de demonstração — quatro casos versionados e executor com validação de rotas;
- [x] executar a demonstração completa pelo menos duas vezes — duas transcrições aprovadas, cada uma com quatro casos e quatro rotas esperadas;
- [ ] criar uma versão candidata à entrega — preparação da `v1.0.0-rc1` iniciada, com manifesto e bloqueadores documentados; avaliação do Dia 12 concluída, restando integração Google AI e entregáveis acadêmicos.

### Entregáveis

- release candidate;
- suíte de testes;
- script de demonstração;
- Docker Compose validado.

### Evidências parciais

- [day13_stabilization.md](../reports/day13_stabilization.md)
- [roteiro de demonstração](../docs/demo_script.md)
- [perguntas de demonstração](../configs/demo_questions.json)
- [checklist da release candidate](../docs/release_candidate.md)
- [manifesto da release candidate](../reports/evidence/release_candidate_manifest.json)
- [executor da demonstração](../scripts/run_demo.ps1)
- [.env.example](../.env.example)
- [requirements.txt](../requirements.txt)
- [requirements-training.txt](../requirements-training.txt)
- [requirements-lock.txt](../requirements-lock.txt)
- [start_medassist.ps1](../scripts/start_medassist.ps1)
- [test_project_bootstrap.py](../tests/unit/test_project_bootstrap.py)

### Critério de aceite

- outra pessoa consegue configurar e executar a aplicação seguindo apenas o README.

---

## 14/09/2026 - README, relatório e vídeo

### Objetivo

Preparar os entregáveis acadêmicos.

### Tarefas do README

- explicar o problema e o escopo;
- apresentar a arquitetura;
- documentar instalação e configuração;
- documentar PostgreSQL e pgvector;
- documentar os providers;
- explicar preparação do dataset;
- explicar fine-tuning, RAG, LangChain e LangGraph;
- documentar execução, testes, segurança e limitações.

### Tarefas do relatório

- descrever a metodologia SDD;
- apresentar análise e curadoria do MedQuAD;
- descrever o fine-tuning;
- apresentar arquitetura e diagramas;
- explicar RAG, PostgreSQL e pgvector;
- explicar segurança e auditoria;
- apresentar avaliação e limitações;
- incluir referências e atribuição ao MedQuAD.

### Tarefas do vídeo

- [x] preparar roteiro de 10 a 12 minutos — roteiro versionado e validado em duas execuções locais;
- demonstrar dataset e curadoria;
- mostrar evidência do fine-tuning;
- executar uma pergunta contextualizada;
- mostrar fontes recuperadas;
- mostrar o fluxo LangGraph;
- demonstrar recusa de prescrição;
- mostrar logs de auditoria;
- mostrar a troca de provider;
- gravar uma primeira versão completa.

### Critério de aceite

- cada requisito do desafio aparece no README, no relatório ou no vídeo;
- o vídeo possui menos de 15 minutos.

---

## 15/09/2026 - Revisão final e entrega

### Objetivo

Validar e entregar sem introduzir novas funcionalidades.

### Tarefas

- não adicionar funcionalidades novas;
- revisar a matriz de rastreabilidade;
- conferir licença e atribuição do MedQuAD;
- revisar referências bibliográficas;
- remover chaves, tokens e arquivos temporários;
- executar notebooks do início ao fim;
- confirmar que as evidências importantes estão salvas;
- testar links e comandos do README;
- recriar o PostgreSQL e o pgvector a partir das migrations;
- executar a demonstração final;
- revisar e exportar o relatório;
- assistir ao vídeo completo;
- criar a tag da entrega;
- realizar a submissão com antecedência;
- confirmar o recebimento da entrega.

### Critério de aceite

- cada requisito obrigatório possui uma evidência rastreável;
- o repositório não contém segredos ou dados pessoais reais;
- todos os arquivos e links da entrega estão acessíveis;
- a submissão foi confirmada.

## Priorização em caso de atraso

Se ocorrer atraso, preservar as entregas nesta ordem:

1. fine-tuning real e reproduzível;
2. LangChain e LangGraph executáveis;
3. RAG com PostgreSQL, pgvector e fontes;
4. segurança, validação humana e auditoria;
5. avaliação comparativa;
6. README e relatório;
7. segundo provider de LLM;
8. interface visual.

Uma CLI ou demonstração por notebook é suficiente para o MVP. A interface visual não deve comprometer os requisitos técnicos obrigatórios.

## Pontos de controle

### Final de 04/09

- especificações criadas;
- MedQuAD analisado e curado;
- PostgreSQL funcionando;
- conjuntos de treino e avaliação definidos.

### Final de 07/09

- baseline registrado;
- fine-tuning executado;
- modelo ou adapter customizado disponível.

Se não houver evidência de fine-tuning até essa data, reduzir imediatamente o número de exemplos, épocas e tamanho do modelo.

### Final de 11/09

- RAG funcional;
- LangChain e LangGraph integrados;
- segurança e auditoria implementadas.

### Final de 13/09

- avaliação concluída;
- testes passando;
- versão candidata à entrega congelada.

### Final de 14/09

- README concluído;
- relatório concluído;
- vídeo gravado;
- entrega pronta apenas para revisão final.
