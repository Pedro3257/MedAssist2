# Arquitetura do MedAssist

**Versão:** 1.0  
**Data:** 01/09/2026

## 1. Visão de contexto

Os diagramas de contexto e execução estão centralizados em [`docs/diagrams.md`](../docs/diagrams.md), evitando versões concorrentes do mesmo fluxo.

O sistema recebe uma pergunta e um identificador sintético, aplica controles de segurança, consulta contexto estruturado e conhecimento vetorial, gera uma resposta fundamentada e registra a decisão. Qualquer sugestão de conduta permanece sujeita a validação humana.

## 2. Componentes

| Componente | Responsabilidade |
|---|---|
| `domain` | Entidades e regras que não dependem de frameworks. |
| `application` | Casos de uso e contratos (repositórios, LLM, auditoria). |
| `infrastructure` | PostgreSQL, configuração e implementações técnicas. |
| `providers` | Adapters de Ollama e Google AI Studio. |
| `rag` | Chunking, embeddings, ingestão e recuperação pgvector. |
| `safety` | Políticas de entrada/saída, urgência e validação humana. |
| `graph` | Estado, nós e rotas do LangGraph. |
| `scripts` / `notebooks` | Pipelines reproduzíveis de dados, treino e avaliação. |

Dependências apontam para dentro: infraestrutura implementa contratos da aplicação; domínio não importa frameworks, banco ou SDKs.

## 3. Fluxo de execução

O [fluxo seguro do LangGraph](../docs/diagrams.md#2-fluxo-seguro-do-langgraph) documenta as rotas de geração, bloqueio, urgência, abstenção e falha controlada.

## 4. Modelo de dados conceitual

- `patients`: pacientes exclusivamente sintéticos.
- `encounters`: atendimentos relacionados ao paciente.
- `exams`: exames realizados e resultados sintéticos.
- `pending_exams`: exames solicitados ainda pendentes.
- `knowledge_documents`: origem, coleção, URL e metadados do MedQuAD.
- `knowledge_chunks`: conteúdo, embedding e vínculo com documento.
- `audit_events`: correlation ID, tempos, decisão, provider, modelo e fontes.

## 5. Pipelines separados

```text
MedQuAD -> curadoria -> splits instrucionais -> LoRA/QLoRA -> adapter customizado
MedQuAD -> curadoria -> documentos/chunks -> embeddings -> pgvector -> retriever
```

Separar os pipelines permite avaliar o efeito do fine-tuning e do RAG de forma independente.

## 6. Decisões arquiteturais

### ADR-001 - MedQuAD como fonte médica do MVP

**Decisão:** usar subconjunto curado do MedQuAD, sugerido no enunciado, preservando coleção, fonte e URL.  
**Motivo:** não há protocolos hospitalares reais disponíveis e eles não devem ser inventados.  
**Consequência:** o projeto demonstra a técnica, mas não representa protocolos de um hospital específico.

### ADR-002 - PostgreSQL com pgvector

**Decisão:** manter dados relacionais, vetores e auditoria no PostgreSQL, usando pgvector para similaridade.  
**Motivo:** simplifica o MVP, oferece transações e mantém metadados e evidências próximos.  
**Consequência:** exige extensão pgvector e migrations reproduzíveis.

### ADR-003 - Ollama e Google AI Studio atrás de contrato comum

**Decisão:** definir `LLMProvider` e selecionar adapter por ambiente.  
**Motivo:** permitir execução local e alternativa remota sem acoplar os casos de uso.  
**Consequência:** capacidades específicas de cada provider ficam isoladas no adapter.

### ADR-004 - LangChain para composição e LangGraph para orquestração

**Decisão:** LangChain compõe prompt/retriever/LLM/parser; LangGraph controla estado, rotas e falhas.  
**Motivo:** atende explicitamente ao desafio e torna caminhos de decisão testáveis.  
**Consequência:** regras clínicas permanecem em `safety`, não escondidas em prompts.

### ADR-005 - LoRA/QLoRA em modelo aberto pequeno

**Decisão:** ajustar um modelo aberto compatível com o hardware, registrando adapter e configuração.  
**Motivo:** obter fine-tuning real e reproduzível no prazo sem treinar um modelo do zero.  
**Consequência:** a escolha final depende da análise de hardware e do piloto.

### ADR-006 - Dados sintéticos e minimização remota

**Decisão:** versionar apenas pacientes/exames sintéticos e enviar ao provider remoto somente o contexto necessário.  
**Motivo:** privacidade, segurança e reprodutibilidade.  
**Consequência:** nenhum desempenho clínico real pode ser alegado.

## 7. Qualidade e segurança

- validação tipada nas fronteiras;
- queries parametrizadas e migrations versionadas;
- timeouts, retries limitados e fallback seguro;
- filtros determinísticos antes e depois da LLM;
- fontes e limiar de recuperação explícitos;
- logs estruturados sem segredos;
- testes unitários, integração e aceite por rota crítica.

