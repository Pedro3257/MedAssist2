# RAG com PostgreSQL e pgvector

**Data planejada:** 08/09/2026  
**Status:** Concluído  
**Base de conhecimento:** MedQuAD curado

## Configuração

- PostgreSQL 16 com pgvector 0.8.6.
- Embeddings `embeddinggemma:300m` via Ollama, com 768 dimensões.
- Distância por cosseno e limiar inicial de 0,55.
- Índice HNSW com `m = 16` e `ef_construction = 64`, medindo 68 MB.

## Preparação e ingestão

| Medida | Quantidade |
|---|---:|
| Pares QA de entrada | 16.339 |
| Documentos | 5.479 |
| Chunks | 17.429 |
| Pares QA divididos | 699 |
| Chunks adicionais pelas divisões | 1.090 |
| Embeddings persistidos | 17.429 |
| Embeddings ausentes | 0 |

Cada chunk mantém foco, pergunta e resposta no conteúdo vetorizado. Coleção, fonte, URL, identificadores e metadados do MedQuAD permanecem disponíveis para proveniência. O pipeline confirma lotes individualmente e ignora chunks já persistidos, permitindo retomada sem duplicatas.

## Recuperação e validação

Cada resultado expõe conteúdo, similaridade, coleção, fonte, URL e identificadores rastreáveis. Sem resultado acima do limiar, o componente sinaliza abstenção.

| Cenário | Resultado |
|---|---|
| Inglês: tratamento de kidney stones | Três resultados relevantes; melhor similaridade 0,6944 |
| Português: tratamento de cálculos renais | Recuperação renal relacionada, porém menos específica |
| Português coloquial: tratamento de pedras nos rins | Cinco resultados relevantes; melhor similaridade 0,6434 |
| Fora do domínio: configuração de Wi-Fi | Abstenção com limiar 0,55 |

- Testes unitários: 4 aprovados.
- Testes de integração real: 3 aprovados.

## Limitações

- O MedQuAD está em inglês; a geração contextualizada será responsável por responder no idioma do usuário.
- O limiar 0,55 deverá ser calibrado com um conjunto maior.
- `Cálculos renais` foi menos específico que `pedras nos rins`; expansão bilíngue, tradução, busca híbrida e reranking são melhorias possíveis.
- Recuperar evidências não comprova validade clínica; as respostas exigem validação humana.

## Evidências reproduzíveis

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
