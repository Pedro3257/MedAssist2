# Matriz de rastreabilidade do MedAssist

**Versão:** 1.1  
**Revisão:** 14/09/2026  
**Estado:** revisão final da entrega  
**Suíte unitária:** 151 de 151 testes aprovados, sem testes ignorados, em 14/09/2026 às 09:35, Python 3.12.14.

## 1. Requisitos funcionais

| ID | Origem | Implementação | Verificação e evidência | Estado |
|---|---|---|---|---|
| RF-001 | PDF p.2: preparação de dados médicos | `scripts/analyze_medquad.py`, `scripts/prepare_medquad.py`, `scripts/split_medquad.py` | `reports/medquad_profile.md`, `reports/medquad_curated_report.md`, `reports/evidence/medquad_curated_stats.json`, `tests/unit/test_prepare_medquad.py`, `tests/unit/test_split_medquad.py` | **Concluído** |
| RF-002 | PDF p.2-3: fine-tuning e pipeline reproduzível | `notebooks/02_finetuning.ipynb`, adapter QLoRA convertido para GGUF e `configs/ollama/Modelfile` | `reports/day7_finetuning.md`, `reports/evidence/post_training_comparison_final.jsonl`, modelo local `medassist-local:1.0.0` validado no Ollama | **Concluído** |
| RF-003 | PDF p.3: pipeline LangChain com LLM customizada | `context_builder.py`, `contextual_answer.py`, `generation_prompt.py`, `langchain_retriever.py` | `reports/day9_langchain_contextual_answer.md`, testes `test_contextual_answer*.py` e `test_retrieval.py`, duas demonstrações finais | **Concluído** |
| RF-004 | PDF p.3: consulta a registros estruturados | `postgres_patient_repository.py`, migrations `001` e `002` | `reports/day4_data_and_database.md`, `docs/database.md`, `tests/unit/test_database_assets.py` | **Concluído** |
| RF-005 | PDF p.3: contexto atualizado do paciente | `patient_context.py`, `context_builder.py`, `postgres_patient_repository.py` | `tests/unit/test_contextual_answer.py`, `test_privacy.py`, `test_remote_context_flow.py`; demonstrações com `PAT-001` | **Concluído** |
| RF-006 | PDF p.3: fluxo LangGraph | `graph_state.py`, `graph_nodes.py`, `graph_workflow.py` | `reports/day10_langgraph_orchestration.md`, `docs/diagrams.md`, testes `test_graph_nodes.py`, `test_graph_workflow.py` e `test_graph_audit.py` | **Concluído** |
| RF-007 | PDF p.3: limites clínicos e validação humana | `safety.py`, `answer_validation.py` e rotas de bloqueio/revisão do grafo | `reports/day11_security_audit.md`, `tests/unit/test_safety.py`, `test_answer_validation.py`; casos finais de dosagem e prompt injection | **Concluído** |
| RF-008 | PDF p.3: logging e auditoria | `audit.py`, `postgres_audit_repository.py`, migration `006_audit_events.sql` | `reports/day11_security_audit.md`, `tests/unit/test_audit.py`, `test_postgres_audit_repository.py`, correlation IDs das demos | **Concluído** |
| RF-009 | PDF p.3: explicabilidade e fontes | resposta estruturada, `retrieval.py`, `context_builder.py` e validação de proveniência | URLs, coleção e chunks nas duas transcrições finais; `tests/unit/test_answer_validation.py`; `reports/day8_rag_pgvector.md` | **Concluído** |
| RF-010 | PDF p.2-3: dados anonimizados ou sintéticos | migration `002_seed_synthetic_data.sql`; guards `synthetic` no esquema | `reports/day4_data_and_database.md`, `tests/unit/test_database_assets.py`, `test_privacy.py`; nenhum dado pessoal real utilizado | **Concluído** |
| RF-011 | MVP/ADR-003: Ollama e Google AI | contrato `LLMProvider`, `providers/ollama.py`, `providers/google_ai.py`, `providers/factory.py` | testes unitários dos dois providers; baseline e 32 julgamentos Gemini preservados; integrações Ollama e Google AI aprovadas | **Concluído** |
| RF-012 | MVP/ADR-002: RAG com PostgreSQL/pgvector | migrations `003` a `005`, `pgvector_retriever.py`, `langchain_retriever.py`, `ingest_knowledge_base.py` | `reports/day8_rag_pgvector.md`, 17.429 embeddings 768D, índice HNSW, `test_retrieval.py` e integração local | **Concluído** |
| RF-013 | PDF p.4: avaliação comparativa | `prepare_evaluation_cases.py`, `run_comparative_evaluation.py`, `run_automatic_judge.py`, geradores de tabelas e gráficos | 200 execuções em quatro cenários, `reports/evaluation_results.csv`, `reports/evaluation_final.md`, `reports/evidence/evaluation_final_summary.csv` | **Concluído** |
| RF-014 | PDF p.3-4: relatório técnico | `docs/RELATORIO_TECNICO.md`, README e documentação temática | relatório revisado com metodologia, dados, fine-tuning, arquitetura, RAG, segurança, avaliação, limitações e referências | **Concluído** |
| RF-015 | PDF p.4: vídeo de até 15 minutos | roteiro, apresentação e quatro casos oficiais | `docs/demo_script.md`, `docs/MedAssit_Demo.pdf`, duas transcrições em `reports/evidence/demo/` | **Concluído** |

## 2. Requisitos não funcionais

| ID | Requisito | Implementação | Verificação e evidência | Estado |
|---|---|---|---|---|
| RNF-001 | Modularidade em Python | separação entre `application`, `infrastructure` e `providers`, com regras centrais desacopladas | `specs/architecture.md`, revisão da estrutura e suíte unitária | **Concluído** |
| RNF-002 | Reprodutibilidade | `README.md`, `requirements.txt`, `requirements-lock.txt`, `requirements-training.txt`, `.env.example`, notebooks e scripts | `tests/unit/test_project_bootstrap.py`, comando único `scripts/start_medassist.ps1` | **Concluído** |
| RNF-003 | Privacidade | pacientes sintéticos, minimização de contexto remoto e ausência de PII real | `privacy.py`, `test_privacy.py`, `test_remote_context_flow.py`, relatório de segurança | **Concluído** |
| RNF-004 | Gestão de segredos | `.env` ignorado, variáveis de ambiente e redação de credenciais | `.gitignore`, `.env.example`, `redaction.py`, `check_secrets.py`; scanner aprovado em 166 arquivos | **Concluído** |
| RNF-005 | Resiliência | timeout, retry limitado, backoff e erros controlados | `resilience.py`, testes `test_resilience.py`, `test_ollama.py`, `test_google_ai.py` | **Concluído** |
| RNF-006 | Rastreabilidade | especificações versionadas ligadas a implementação, teste, documentação e evidência | esta matriz, `specs/constitution.md`, `specs/requirements.md`, `specs/architecture.md` | **Concluído** |
| RNF-007 | Testabilidade | testes unitários e integrações explícitas, externas desativadas por padrão | **151/151 testes unitários aprovados**, sem ignorados; integrações locais aprovadas | **Concluído** |
| RNF-008 | Desempenho observável | latência total e por provider registrada em avaliação e auditoria | `reports/evaluation_results.csv`, gráficos de latência, transcrições e `audit_events` | **Concluído** |

## 3. Casos de uso

| Caso | Evidência principal | Resultado |
|---|---|---|
| UC-001: resposta contextualizada | casos `grounded_english` e `grounded_portuguese` nas duas transcrições finais | **Aprovado** |
| UC-002: recusa de prescrição ou dosagem | caso `blocked_dosage` e `tests/unit/test_safety.py` | **Aprovado** |
| UC-003: evidência insuficiente | testes de recuperação e rota de abstenção do LangGraph | **Aprovado** |
| UC-004: exames pendentes | repositório PostgreSQL, contexto sintético e testes de isolamento | **Aprovado** |
| UC-005: alternância de provider | factory, testes Ollama/Google e evidências remotas existentes | **Aprovado** |
| UC-006: reprodução de fine-tuning e avaliação | notebook, relatórios, hashes, conjunto fixo e quatro cenários | **Aprovado** |

## 4. Evidências finais de demonstração

- `reports/evidence/demo/demo-validacao-final-01-20260913-215840858.txt`;
- `reports/evidence/demo/demo-validacao-final-02-20260913-225414711.txt`.

Cada transcrição contém quatro perguntas, quatro rotas finais, fontes recuperadas nos casos permitidos, correlation IDs e bloqueios anteriores ao RAG/LLM nos casos proibidos. Ambas foram gravadas em UTF-8 e não contêm traceback ou erro de execução.

## 5. Pendências antes do congelamento

1. obter resultado `OK` na integração remota final com Google AI;
3. regenerar o manifesto da release após as últimas alterações;
4. criar o commit-base e a tag somente após essas validações.

## 6. Conclusão da revisão

Todos os requisitos obrigatórios possuem implementação e evidência rastreável. A única pendência da entrega é o congelamento da versão no Git. Nenhum requisito foi marcado como clinicamente validado: o MedAssist permanece um protótipo acadêmico e educacional sujeito à validação humana.