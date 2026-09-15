# Proposta de organização do trabalho em dupla

**Projeto:** MedAssist - Tech Challenge FIAP, Fase 3  
**Data da proposta:** 01/09/2026  
**Status:** Rascunho para discussão entre os integrantes

> Este documento não altera o cronograma oficial em `DAILY_SCHEDULE.md`. Ele apresenta uma sugestão de responsabilidades para ser analisada e aprovada pela dupla.

## 1. Princípio da divisão

A proposta divide o projeto em duas trilhas técnicas relacionadas, evitando alternar dias ou fragmentar um mesmo componente entre várias pessoas:

- **Integrante A:** dados, fine-tuning e avaliação;
- **Integrante B:** aplicação, banco de dados, RAG e orquestração;
- **Ambos:** segurança, integração, documentação e entrega.

Os nomes podem ser associados às trilhas depois da conversa. Caso um integrante tenha maior experiência com Machine Learning, ele deve preferencialmente assumir a Trilha A; quem tiver maior experiência com desenvolvimento de aplicações, banco de dados ou arquitetura deve assumir a Trilha B.

## 2. Distribuição diária sugerida

| Data | Integrante A - Dados e modelos | Integrante B - Aplicação e infraestrutura | Trabalho conjunto |
|---|---|---|---|
| 01/09 | Apresentar a estratégia de curadoria, fine-tuning e avaliação | Revisar arquitetura, banco e fluxo da aplicação | Revisar o Dia 1 concluído e alinhar o escopo |
| 02/09 | Executar a análise completa do MedQuAD | Revisar licença, estrutura e necessidades futuras de ingestão | Aprovar as coleções do MVP |
| 03/09 | Implementar parser, normalização, deduplicação e dataset curado | Revisar o contrato de saída e preparar a integração | Validar amostras e critérios de exclusão |
| 04/09 | Criar os conjuntos de treino, validação, teste e avaliação | Configurar Docker Compose, PostgreSQL, migrations e dados sintéticos | Testar vazamento dos conjuntos e consultas por paciente |
| 05/09 | Preparar o conjunto de baseline e a coleta de métricas | Implementar `LLMProvider`, Ollama, Google AI Studio, timeout e retry | Executar e conferir o baseline |
| 06/09 | Executar o fine-tuning piloto e registrar evidências | Consolidar providers e preparar a integração com o modelo ajustado | Validar inferência com o adapter piloto |
| 07/09 | Executar o fine-tuning definitivo, gerar adapter e métricas | Integrar o modelo customizado ao fluxo local | Realizar smoke tests e comparar modelo-base e ajustado |
| 08/09 | Preparar documentos e chunks e apoiar a escolha de embeddings | Implementar pgvector, ingestão, índice e retriever | Testar recuperação em português e inglês |
| 09/09 | Avaliar a qualidade do contexto e das respostas | Implementar LangChain, consulta de paciente, exames, RAG, prompt e parser | Executar testes de integração ponta a ponta |
| 10/09 | Criar casos de teste para as diferentes rotas | Implementar estado, nós e rotas do LangGraph | Executar e registrar os caminhos do grafo |
| 11/09 | Criar casos proibidos, urgências e prompt injection | Implementar segurança, validação de saída, auditoria e minimização de dados | Fazer revisão cruzada dos controles de segurança |
| 12/09 | Liderar a avaliação comparativa e a análise dos resultados | Automatizar execução, latência, fontes e coleta de resultados | Realizar avaliação humana das respostas |
| 13/09 | Executar testes de datasets, modelo e avaliação | Executar testes de banco, RAG, providers e aplicação | Realizar duas demonstrações completas |
| 14/09 | Redigir dataset, fine-tuning, avaliação e limitações | Redigir arquitetura, banco, RAG, LangChain, LangGraph e segurança | Concluir README, diagramas, roteiro e gravação |
| 15/09 | Revisar evidências de dados e modelo | Recriar o ambiente e revisar evidências da aplicação | Executar demonstração final, revisar vídeo e relatório e realizar a submissão |

## 3. Trilha A - Dados, modelo e avaliação

### Responsabilidades principais

- analisar e documentar o MedQuAD;
- implementar a preparação e curadoria dos dados;
- produzir os conjuntos `train`, `validation`, `test` e `evaluation`;
- configurar e executar o fine-tuning com LoRA ou QLoRA;
- registrar hiperparâmetros, seeds, ambiente, loss, duração e uso de memória;
- salvar, identificar e testar o adapter customizado;
- executar o baseline e a avaliação comparativa;
- produzir tabelas, gráficos e análise dos resultados;
- redigir as seções científicas do relatório.

### Áreas e artefatos predominantes

- `notebooks/`;
- `scripts/prepare_medquad.py`;
- configurações de treinamento;
- datasets curados e conjuntos de avaliação;
- adapter e evidências de fine-tuning;
- `reports/evaluation_results.csv`;
- gráficos e análise comparativa.

### Requisitos relacionados

- `RF-001` - preparação e curadoria dos dados;
- `RF-002` - fine-tuning da LLM;
- `RF-013` - avaliação comparativa;
- parte de `RF-014` - relatório técnico.

## 4. Trilha B - Aplicação e infraestrutura

### Responsabilidades principais

- configurar Docker Compose, PostgreSQL e migrations;
- modelar e carregar pacientes, atendimentos e exames sintéticos;
- implementar os adapters Ollama e Google AI Studio;
- implementar configuração, timeout, retry e tratamento de falhas;
- configurar pgvector, ingestão e busca por similaridade;
- implementar o pipeline LangChain;
- implementar o estado, os nós e as rotas do LangGraph;
- implementar persistência de auditoria e observabilidade;
- documentar instalação, arquitetura e execução da aplicação.

### Áreas e artefatos predominantes

- `src/medassist/infrastructure`;
- `src/medassist/providers`;
- `src/medassist/rag`;
- `src/medassist/graph`;
- `migrations/`;
- `compose.yaml`;
- `.env.example`;
- testes de integração da aplicação.

### Requisitos relacionados

- `RF-003` a `RF-006` - LangChain, dados estruturados, contexto e LangGraph;
- `RF-008` - auditoria;
- `RF-011` - providers de LLM;
- `RF-012` - RAG com PostgreSQL e pgvector;
- parte de `RF-014` - relatório técnico.

## 5. Responsabilidades compartilhadas

Os seguintes itens devem ser implementados ou revisados pelos dois integrantes:

- `RF-007` - segurança clínica e validação humana;
- `RF-009` - explicabilidade e apresentação de fontes;
- `RF-010` - dados sintéticos e privacidade;
- `RF-014` - relatório técnico final;
- `RF-015` - roteiro, gravação e revisão do vídeo;
- testes de integração entre as duas trilhas;
- atualização da rastreabilidade e preservação de evidências;
- revisão final do escopo e dos critérios de aceite.

A pessoa que implementar uma funcionalidade deve escrever os testes básicos. A outra pessoa deve revisar a implementação e tentar reproduzir o resultado de forma independente.

## 6. Contratos de integração

Antes de iniciar o desenvolvimento paralelo, a dupla deve concordar sobre quatro contratos.

### 6.1 Saída da curadoria

Definir o esquema do JSONL, incluindo:

- identificador estável;
- pergunta e resposta;
- tipo e foco;
- fonte e URL;
- coleção;
- UMLS CUI, quando disponível.

### 6.2 Interface do provider

Definir a entrada e a saída de `LLMProvider`, incluindo:

- prompt e parâmetros de geração;
- texto gerado;
- provider e modelo;
- latência;
- tratamento padronizado de erros;
- metadados necessários à auditoria.

### 6.3 Contexto do RAG

Definir como o retriever entrega:

- conteúdo recuperado;
- similaridade;
- coleção;
- fonte;
- URL;
- identificador do documento ou chunk.

### 6.4 Estado do LangGraph

Definir campos para:

- pergunta;
- identificador e contexto mínimo do paciente;
- exames e exames pendentes;
- evidências recuperadas;
- decisão de segurança;
- resposta estruturada;
- fontes;
- necessidade de validação humana;
- dados de auditoria e falhas.

## 7. Rotina de colaboração sugerida

- usar uma branch por tarefa curta;
- evitar branches abertas por vários dias;
- solicitar revisão do outro integrante antes de integrar mudanças relevantes;
- realizar uma conversa diária de aproximadamente 15 minutos sobre progresso, bloqueios e dependências;
- atualizar testes, evidências e documentação junto com a implementação;
- realizar integrações conjuntas ao final de 04/09, 07/09, 11/09 e 13/09;
- não aprovar individualmente decisões relacionadas a prescrição, urgência, privacidade ou validação humana.

## 8. Critério de conclusão do trabalho

Uma atividade somente deve ser considerada concluída quando possuir:

1. requisito ou especificação correspondente;
2. implementação reproduzível;
3. teste ou demonstração executada;
4. evidência registrada;
5. documentação mínima;
6. revisão do outro integrante quando afetar a integração ou a segurança.

## 9. Pontos para decidir na conversa

- qual integrante assumirá a Trilha A e qual assumirá a Trilha B;
- disponibilidade diária de cada integrante;
- hardware disponível para o fine-tuning;
- responsável pelas credenciais do Google AI Studio;
- estratégia de branches e revisão;
- local compartilhado para artefatos grandes que não devem entrar no Git;
- divisão da apresentação e das falas no vídeo;
- como registrar a avaliação humana das respostas;
- horário dos pontos de integração e da revisão final.

