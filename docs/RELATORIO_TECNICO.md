# Relatório Técnico

## Dados do aluno

- **Nome:** Ari Monteiro
- **Turma:** 9IADT
- **RA:** 371705
- **Contato:** ari_mont@yahoo.com.br

## Vídeo de demonstração

A apresentação e a demonstração funcional do MedAssist estão disponíveis no YouTube:

[Assistir à demonstração do MedAssist](https://youtu.be/98nxrPxlC5c)

## MedAssist | Medical Assistant 1.0.0

O MedAssist é um MVP acadêmico de assistência informacional médica. A solução combina fine-tuning de modelo aberto, recuperação aumentada por geração (RAG), LangChain, LangGraph, PostgreSQL/pgvector, múltiplos providers de LLM e controles determinísticos de segurança.

O projeto foi concebido para demonstrar como um modelo ajustado pode responder perguntas com apoio de uma base médica rastreável e de registros sintéticos de pacientes. O sistema valida a entrada, aplica regras de segurança, recupera contexto, gera uma resposta, valida a saída e registra a decisão para auditoria. Toda resposta médica gerada permanece condicionada à validação humana.

> **Aviso:** o MedAssist é um protótipo educacional. Não é um dispositivo médico, não realiza diagnóstico, não prescreve tratamentos e não substitui a avaliação de um profissional de saúde habilitado.

O escopo funcional, os critérios de aceite e as restrições estão detalhados em [`specs/requirements.md`](../specs/requirements.md). A execução local está documentada no [`README.md`](../README.md).

## A metodologia SDD

O desenvolvimento adotou *Specification-Driven Development* (SDD), utilizando especificações versionadas como referência para implementação e verificação. Antes da construção dos componentes, foram definidos princípios não negociáveis, requisitos funcionais e não funcionais, arquitetura, casos de uso e critérios de aceite.

A aplicação da metodologia foi organizada em quatro artefatos:

- [`specs/constitution.md`](../specs/constitution.md): princípios de segurança clínica, privacidade, explicabilidade, rastreabilidade, reprodutibilidade, modularidade e controle de escopo;
- [`specs/requirements.md`](../specs/requirements.md): requisitos verificáveis e casos de uso;
- [`specs/architecture.md`](../specs/architecture.md): componentes, limites de dependência e decisões arquiteturais;
- [`specs/traceability.md`](../specs/traceability.md): relação entre requisito, implementação, teste e evidência.

Nesse processo, uma funcionalidade não é considerada concluída apenas porque seu código foi escrito. Ela precisa possuir especificação correspondente, implementação reproduzível, verificação automatizada ou demonstração, evidência e documentação mínima. Essa regra foi especialmente importante para impedir que decisões de conveniência superassem requisitos de segurança e privacidade.

O SDD também auxiliou a controlar o escopo. O projeto priorizou um fluxo executável por CLI, dados exclusivamente sintéticos, um banco PostgreSQL único e integração por contratos, deixando interface web, dados hospitalares reais e implantação em nuvem fora do MVP.

## O dataset MedQuAD

O [MedQuAD](https://github.com/abachaa/MedQuAD) é um conjunto público de perguntas e respostas médicas originadas de sites dos National Institutes of Health e de outras fontes de saúde. Seus arquivos XML agrupam um tema principal em `Focus` e perguntas e respostas em elementos `QAPair`.

A inspeção percorreu 11.274 arquivos XML distribuídos em 12 coleções. Foram observados 47.441 pares, mas parte considerável pertence a coleções cujas respostas foram removidas por restrições de copyright. Essas coleções foram contabilizadas e excluídas do conteúdo utilizado.

O pipeline de curadoria processou 16.412 pares candidatos e produziu 16.339 registros válidos e únicos. Entre as exclusões estavam cinco respostas ausentes, uma resposta abaixo do tamanho mínimo, cinco documentos sem identificador, 14 registros sem foco e 48 duplicatas exatas. O resultado completo e as estatísticas por coleção estão em:

- [`reports/medquad_profile.md`](../reports/medquad_profile.md);
- [`reports/medquad_curated_report.md`](../reports/medquad_curated_report.md);
- [`reports/evidence/medquad_curated_stats.json`](../reports/evidence/medquad_curated_stats.json).

A preparação normaliza Unicode, entidades HTML, markup residual e espaços; valida comprimentos e campos obrigatórios; preserva fonte, URL, coleção, caminho XML e metadados UMLS; e cria identificadores estáveis por SHA-256. O JSONL foi escolhido porque permite processar cada registro independentemente, facilita retomadas e evita carregar o conjunto inteiro em memória.

Para reduzir vazamento entre treino e avaliação, a divisão foi realizada por foco médico, e não apenas por linha. Assim, perguntas sobre a mesma entidade não são distribuídas entre treino, validação e teste. Os conjuntos finais possuem 4.795 exemplos de treino, 603 de validação e 602 de teste.

O conteúdo permanece majoritariamente em inglês. A tradução integral e a criação de um corpus médico validado em português foram mantidas como trabalho futuro, evitando introduzir traduções automáticas não revisadas no treinamento principal.

## O processo de fine-tuning

O fine-tuning utilizou `meta-llama/Llama-3.2-1B-Instruct` e a técnica QLoRA. O modelo-base foi carregado em 4 bits com NF4 e *double quantization*, enquanto adapters LoRA foram aplicados às projeções de atenção e MLP. A configuração usou rank 8, alpha 16, dropout 0,05, seed 42 e comprimento máximo de 1.024 tokens.

O treinamento definitivo foi executado no Kaggle com GPU Tesla T4:

| Parâmetro | Resultado |
|---|---:|
| Registros de treino | 4.795 |
| Registros de validação | 603 |
| Registros de teste usados no treino | 0 |
| Épocas | 1 |
| Batch efetivo | 8 |
| Passos do otimizador | 600 |
| Tempo total | 43,38 minutos |
| Pico de VRAM | 2,58 GB |
| Loss final de treino | 1,357977 |
| Melhor loss de validação | 1,321857 |
| Mean token accuracy no passo 600 | 0,687311 |

A redução da loss de validação ao longo da época demonstra que houve aprendizado, mas não comprova precisão clínica. O conjunto de teste permaneceu isolado do treinamento.

O adapter PEFT foi salvo em Safetensors, empacotado com metadados e convertido para GGUF F16 com o conversor oficial do `llama.cpp`. Em seguida, foi combinado ao `llama3.2:1b` pelo Ollama, originando `medassist-local:1.0.0`. Os hashes SHA-256 permitem confirmar a integridade dos artefatos.

O notebook reproduzível está em [`notebooks/02_finetuning.ipynb`](../notebooks/02_finetuning.ipynb). Configuração, métricas, hashes e smoke tests estão consolidados no [relatório de fine-tuning](../reports/day7_finetuning.md), e o procedimento de inferência local está em [`docs/ollama.md`](ollama.md).

## A arquitetura da solução

A solução segue separação entre domínio, aplicação e infraestrutura. Entidades e regras centrais não dependem de frameworks; casos de uso dependem de contratos; PostgreSQL, Ollama e Google AI implementam esses contratos nas bordas.

Os principais módulos são:

- `domain`: entidades e validações independentes;
- `application`: casos de uso, segurança, contexto, auditoria e nós do grafo;
- `infrastructure`: configuração e repositórios PostgreSQL;
- `providers`: contrato `LLMProvider` e adapters Ollama e Google AI;
- `rag`: embeddings, recuperação vetorial e integração LangChain;
- `migrations`: esquema, dados sintéticos, pgvector e auditoria;
- `scripts` e `notebooks`: pipelines reproduzíveis de dados, treinamento, avaliação e demonstração.

O [`LLMProvider`](../src/medassist/application/llm.py) desacopla geração e orquestração. O provider padrão usa o modelo ajustado no Ollama, enquanto o Google AI demonstra portabilidade remota. O `embeddinggemma:300m` gera vetores; o `gemma3:4b` atua somente como revisor de idioma quando uma resposta local precisa ser apresentada em português; e o `qwen2.5:7b-instruct` é usado exclusivamente como avaliador offline.

O LangChain compõe recuperação, contexto, prompt, provider e parser. O LangGraph mantém estado tipado e controla as rotas de entrada inválida, bloqueio, urgência, paciente inexistente, contexto insuficiente, erro do provider e resposta destinada à validação humana.

A visão dos componentes e o fluxo completo estão centralizados em [`docs/diagrams.md`](diagrams.md). As decisões arquiteturais e suas consequências permanecem em [`specs/architecture.md`](../specs/architecture.md).

## A implementação do RAG

O RAG utiliza PostgreSQL 16 com pgvector 0.8.6. A escolha de um único banco permite armazenar contexto relacional, conhecimento vetorial e auditoria com transações e proveniência comuns, sem adicionar outro serviço ao MVP.

A base de conhecimento foi construída a partir dos 16.339 registros curados do MedQuAD. Perguntas e respostas relacionadas foram agrupadas em 5.479 documentos e divididas em 17.429 chunks. O processo gerou 17.429 embeddings de 768 dimensões com `embeddinggemma:300m`; nenhum embedding ficou ausente.

Cada chunk preserva foco, pergunta, resposta, coleção, fonte, URL e identificadores. A busca usa distância por cosseno, limiar inicial de similaridade 0,55 e índice HNSW configurado com `m = 16` e `ef_construction = 64`. A ingestão é retomável: lotes confirmados e chunks existentes não são duplicados.

A recuperação foi validada com perguntas em inglês e português. Consultas médicas recuperaram fontes relacionadas; uma pergunta fora do domínio produziu abstenção. As diferenças entre “cálculos renais” e “pedras nos rins” também evidenciaram limitações da busca puramente vetorial e motivaram propostas futuras de expansão bilíngue, busca híbrida e reranking.

O contexto final combina somente os dados do paciente sintético solicitado e as evidências acima do limiar. Se nenhuma evidência for suficiente, a LLM não é chamada. Quando há geração, a resposta apresenta fontes e permanece marcada para validação humana.

O esquema e as consultas estão em [`docs/database.md`](database.md). Configuração, medidas, testes e limitações da recuperação estão no [relatório do RAG](../reports/day8_rag_pgvector.md). Os diagramas ficam em [`docs/diagrams.md`](diagrams.md).

## Segurança e auditoria da solução

A segurança foi implementada em camadas determinísticas, sem depender apenas do comportamento probabilístico da LLM.

Antes da consulta ao banco ou da geração, o sistema:

- valida formato e conteúdo mínimo da entrada;
- bloqueia pedidos de prescrição, dosagem individualizada e diagnóstico definitivo;
- recusa tentativas básicas de revelar ou substituir instruções internas;
- identifica possíveis urgências e devolve orientação controlada;
- impede que um paciente inválido avance para recuperação ou geração.

Depois da geração, a resposta e sua proveniência são novamente validadas. Respostas geradas precisam possuir fontes HTTP ou HTTPS válidas, pertencer ao paciente solicitado e não podem introduzir dosagem explícita. Uma resposta aprovada tecnicamente ainda segue para a rota `human_validation`.

O provider remoto recebe uma representação minimizada do contexto. Nome, ID do paciente, data de nascimento, IDs internos e datas exatas são removidos; permanecem somente informações clínicas necessárias. Chaves Google, tokens Bearer, senhas e blocos de chave privada são redigidos antes da persistência de perguntas, erros ou eventos.

A migration [`006_audit_events.sql`](../migrations/006_audit_events.sql) criou a estrutura de auditoria. Cada execução registra correlation ID, timestamp, paciente sintético quando válido, pergunta redigida, decisão, provider, modelo, fontes, latência, necessidade de validação humana, erro e sequência de nós. A resposta completa não é armazenada.

A suíte atual possui 151 testes unitários aprovados. Ela cobre políticas clínicas, prompt injection, validação de saída, minimização remota, redação de segredos, repositórios, providers, RAG e rotas do LangGraph. O scanner de segredos compara arquivos oficiais com valores sensíveis locais sem imprimir os valores encontrados. A implementação e as evidências estão detalhadas no [relatório de segurança e auditoria](../reports/day11_security_audit.md).

## Avaliação final, limitações e trabalhos futuros

A avaliação utiliza um conjunto fixo com 40 casos médicos e 10 casos de segurança. Os mesmos 50 casos foram executados em quatro cenários:

1. modelo-base sem RAG;
2. modelo ajustado sem RAG;
3. modelo-base com RAG;
4. modelo ajustado com RAG.

As 200 execuções registraram resposta, decisão, fontes, latência e métricas determinísticas. Dez respostas médicas de cada cenário, totalizando 40, receberam avaliação qualitativa automática com `qwen2.5:7b-instruct`. O avaliador atribuiu notas de 1 a 5 para relevância, correção, completude e groundedness e marcou possíveis alucinações. Trinta e dois julgamentos obtidos anteriormente com `gemini-3.6-flash` foram preservados como comparação complementar.

| Cenário | Relevância | Correção | Completude | Groundedness | Possível alucinação |
|---|---:|---:|---:|---:|---:|
| Base sem RAG | 1,90 | 1,70 | 2,50 | N/A | 9/10 |
| Ajustado sem RAG | 2,30 | 2,00 | 2,10 | N/A | 9/10 |
| Base com RAG | 3,80 | 3,40 | 3,00 | 4,67 | 4/10 |
| Ajustado com RAG | 4,60 | 4,40 | 4,10 | 4,70 | 1/10 |

O cenário ajustado com RAG obteve as maiores médias em todas as dimensões aplicáveis. No subconjunto comum aos dois avaliadores, a diferença absoluta média entre notas Qwen e Gemini foi 0,674 ponto, com 87,5% de concordância na indicação de alucinação.

Os resultados sugerem que fine-tuning e RAG, combinados, melhoraram a qualidade no conjunto observado. Eles não isolam causalidade nem demonstram segurança ou eficácia clínica. A avaliação qualitativa foi realizada por outra LLM, não por profissional de saúde; métricas lexicais não medem validade clínica; o MedQuAD pode conter conteúdo desatualizado; e diferenças de idioma afetam comparações. Houve ainda uma falha controlada de geração no cenário base com RAG.

A análise completa, os gráficos e os casos negativos estão em [`reports/evaluation_final.md`](../reports/evaluation_final.md). Os resultados tabulares permanecem em [`reports/evaluation_results.csv`](../reports/evaluation_results.csv) e [`reports/evidence/evaluation_final_summary.csv`](../reports/evidence/evaluation_final_summary.csv).

### Trabalhos futuros

- criar e validar um corpus médico em português para fine-tuning multilíngue;
- submeter respostas e critérios de segurança à revisão de profissionais de saúde;
- atualizar e ampliar as fontes médicas além do MedQuAD;
- combinar busca vetorial com busca lexical, expansão de consulta e reranking;
- calibrar limiares de similaridade com conjunto maior e mais diverso;
- avaliar modelos maiores, diferentes quantizações e mais épocas de treinamento;
- ampliar pacientes e cenários sintéticos sem introduzir dados pessoais reais;
- criar interface autenticada e políticas de acesso antes de qualquer uso institucional;
- monitorar deriva, qualidade das fontes e comportamento por idioma;
- realizar avaliação de segurança e conformidade apropriada antes de qualquer aplicação fora do contexto acadêmico.

## Referências

1. BEN ABACHA, Asma; DEMNER-FUSHMAN, Dina. *A Question-Entailment Approach to Question Answering*. BMC Bioinformatics, v. 20, artigo 511, 2019. DOI: [10.1186/s12859-019-3119-4](https://doi.org/10.1186/s12859-019-3119-4).
2. BEN ABACHA, Asma; DEMNER-FUSHMAN, Dina. *MedQuAD: Medical Question Answering Dataset*. GitHub. Disponível em: [github.com/abachaa/MedQuAD](https://github.com/abachaa/MedQuAD). Dataset distribuído sob licença [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
3. HU, Edward J. et al. *LoRA: Low-Rank Adaptation of Large Language Models*. 2021. Disponível em: [arXiv:2106.09685](https://arxiv.org/abs/2106.09685).
4. DETTMERS, Tim et al. *QLoRA: Efficient Finetuning of Quantized LLMs*. 2023. Disponível em: [arXiv:2305.14314](https://arxiv.org/abs/2305.14314).
5. META. *Llama 3.2*. Documentação do modelo-base disponível no [Hugging Face](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct).
6. LANGCHAIN. *LangChain documentation*. Disponível em: [python.langchain.com](https://python.langchain.com/docs/introduction/).
7. LANGCHAIN. *LangGraph documentation*. Disponível em: [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/).
8. PGVECTOR. *Open-source vector similarity search for Postgres*. Disponível em: [github.com/pgvector/pgvector](https://github.com/pgvector/pgvector).
9. OLLAMA. *Ollama documentation*. Disponível em: [docs.ollama.com](https://docs.ollama.com/).
10. POSTGRESQL GLOBAL DEVELOPMENT GROUP. *PostgreSQL 16 documentation*. Disponível em: [postgresql.org/docs/16](https://www.postgresql.org/docs/16/).
