# Requisitos do MedAssist

**Versão:** 1.0  
**Data:** 01/09/2026  
**Fonte primária:** `docs/8IADT - Fase 3 - Tech challenge.pdf`, páginas 2 a 4.

## 1. Visão e premissas

O MedAssist é um assistente médico acadêmico que responde dúvidas clínicas, consulta dados sintéticos de pacientes, recupera conhecimento médico e coordena um fluxo seguro de apoio à decisão. O enunciado descreve dados internos hospitalares; como o projeto não dispõe de dados reais, o MVP usa o MedQuAD como conteúdo público equivalente e registros sintéticos como demonstração anonimizada.

### Atores

- **Profissional de saúde:** formula perguntas e valida qualquer possível conduta.
- **Avaliador acadêmico:** reproduz pipelines e confere as evidências.
- **Administrador técnico:** configura banco, providers e modelos.

## 2. Requisitos funcionais obrigatórios

| ID | Requisito | Critério de aceite verificável |
|---|---|---|
| RF-001 | Preparar e curar dados médicos para treinamento. | Pipeline remove entradas inválidas/duplicadas, preserva fonte, anonimiza ou usa dados sintéticos e produz conjuntos reproduzíveis. |
| RF-002 | Realizar fine-tuning de uma LLM com exemplos médicos. | Um adapter LoRA/QLoRA é treinado, salvo e carregado em inferência; modelo-base, seed, configuração e métricas ficam registrados. |
| RF-003 | Integrar a LLM customizada em pipeline LangChain. | Uma pergunta percorre prompt, LLM customizada e parser por uma cadeia executável. |
| RF-004 | Consultar base estruturada de pacientes e registros. | Dado um identificador sintético válido, o sistema retorna apenas paciente, atendimentos e exames correspondentes. |
| RF-005 | Contextualizar respostas com dados atualizados do paciente. | A resposta inclui o contexto atual recuperado e não mistura dados de pacientes distintos. |
| RF-006 | Coordenar decisões em fluxo LangGraph. | O grafo executa e testa rotas de sucesso, bloqueio de segurança, paciente inexistente, evidência insuficiente e falha de provider. |
| RF-007 | Impedir sugestões clínicas impróprias. | Pedidos de prescrição, dosagem ou diagnóstico definitivo são recusados e encaminhados para validação humana. |
| RF-008 | Registrar logs detalhados para auditoria. | Cada execução gera evento com correlation ID, timestamp, decisão, provider, modelo, fontes e latência, sem segredo. |
| RF-009 | Explicar respostas por fontes. | Respostas fundamentadas apresentam fonte e URL; ausência de evidência suficiente produz abstenção explícita. |
| RF-010 | Disponibilizar dataset anonimizado ou sintético. | Repositório contém dados de demonstração exclusivamente sintéticos, identificados como tal e sem PII real. |
| RF-011 | Suportar Ollama e Google AI Studio. | Provider é selecionável por configuração e ambos cumprem o mesmo contrato sem alteração dos casos de uso. |
| RF-012 | Recuperar conhecimento por RAG com PostgreSQL/pgvector. | Busca retorna conteúdo, similaridade, coleção, fonte e URL; pergunta sem evidência pode se abster. |
| RF-013 | Produzir avaliação comparativa do modelo. | Casos fixos comparam modelo-base/ajustado com/sem RAG e registram qualidade, segurança, fontes e latência. |
| RF-014 | Produzir relatório técnico detalhado. | Relatório explica fine-tuning, assistente, fluxo LangChain/LangGraph, avaliação, resultados e limitações. |
| RF-015 | Demonstrar o sistema em vídeo de até 15 minutos. | Vídeo mostra treinamento/modelo customizado, fluxo automatizado, pergunta contextualizada, logs e validação. |

## 3. Requisitos não funcionais

| ID | Requisito | Critério de aceite verificável |
|---|---|---|
| RNF-001 | Modularidade em Python. | Pacotes separam domínio, aplicação, infraestrutura, providers, RAG, grafo e segurança; dependências respeitam esses limites. |
| RNF-002 | Reprodutibilidade. | README documenta configuração e comandos; pipelines registram dependências, seeds e versões. |
| RNF-003 | Privacidade. | Nenhum dado pessoal real é usado; transmissão remota e logs são minimizados. |
| RNF-004 | Gestão de segredos. | Chaves vêm de variáveis de ambiente; `.env` é ignorado; varredura do repositório não encontra credenciais. |
| RNF-005 | Resiliência. | Providers possuem timeout, retry limitado e erro controlado; indisponibilidade não gera resposta clínica inventada. |
| RNF-006 | Rastreabilidade. | Todo requisito obrigatório aponta para implementação, teste, documentação e evidência planejada. |
| RNF-007 | Testabilidade. | Regras críticas possuem testes unitários; banco, RAG, providers e grafo possuem testes de integração/aceite. |
| RNF-008 | Desempenho observável. | Latência total e por provider é registrada e comparada na avaliação, sem meta clínica de tempo real. |

## 4. Casos de uso e aceite

### UC-001 - Responder pergunta clínica contextualizada

**Pré-condições:** paciente sintético existente, banco disponível e provider configurado.  
**Fluxo principal:** validar entrada; aplicar segurança; buscar paciente/exames; recuperar fontes; gerar resposta; validar saída; registrar auditoria.  
**Aceite:** resposta usa o paciente correto, apresenta fontes e informa que qualquer conduta exige validação humana.

### UC-002 - Recusar prescrição ou dosagem

**Fluxo:** detectar intenção proibida; não chamar geração clínica; retornar recusa segura; registrar decisão.  
**Aceite:** nenhum medicamento, dose ou prescrição individual é fornecido e a auditoria marca o bloqueio.

### UC-003 - Tratar evidência insuficiente

**Fluxo:** executar recuperação; comparar relevância com limiar; abster-se quando insuficiente; registrar fontes/ausência.  
**Aceite:** o sistema não inventa resposta e recomenda consulta a fonte ou profissional apropriado.

### UC-004 - Consultar exames pendentes

**Fluxo:** localizar paciente; consultar exames pendentes; compor contexto mínimo; apresentar informação sem decidir conduta.  
**Aceite:** apenas exames do paciente informado aparecem e não há exposição de outro registro.

### UC-005 - Alternar provider de LLM

**Fluxo:** selecionar provider por variável de ambiente; executar a mesma interface; registrar provider/modelo.  
**Aceite:** Ollama e Google AI Studio são alternados sem editar os casos de uso.

### UC-006 - Reproduzir fine-tuning e avaliação

**Fluxo:** preparar dados; treinar adapter; executar inferência; rodar conjunto fixo; gerar resultados.  
**Aceite:** comandos, configurações e artefatos permitem repetir o processo e comparar os quatro cenários definidos.

## 5. Fora do escopo

- dados reais de pacientes, integração hospitalar ou uso clínico;
- prescrição, diagnóstico definitivo ou decisão autônoma;
- classificador de sepse;
- autenticação hospitalar, microsserviços, nuvem ou interface web sofisticada;
- tradução integral do MedQuAD ou treinamento de LLM do zero.

## 6. Definição de pronto

Um requisito só muda para **Concluído** quando há implementação reproduzível, teste/demonstração executada, evidência registrada e documentação mínima, além do critério de aceite satisfeito.

