# Dia 10 — Orquestração com LangGraph

**Data planejada:** 10/09/2026  
**Validação final:** 12/09/2026  
**Status:** concluído

## Resultado

O pipeline do MedAssist foi organizado em um `StateGraph` compilado com estado
tipado e dependências injetadas. O grafo coordena validação de entrada,
segurança inicial, consulta do paciente e dos exames, recuperação RAG,
composição do contexto, geração, validação humana e auditoria em memória.

## Nós implementados

1. `validate_input`: normaliza e valida paciente e pergunta;
2. `safety`: bloqueia solicitações explícitas de diagnóstico, prescrição ou
   dosagem;
3. `patient`: recupera paciente, atendimentos e exames sintéticos;
4. `retrieval`: recupera evidências pelo adapter LangChain/pgvector;
5. `context`: mantém dados do paciente separados das evidências;
6. `generation`: gera resposta, fallback ou falha controlada;
7. `validate_answer`: verifica paciente, fontes e validação humana;
8. `audit`: registra a decisão final sem conteúdo clínico ou segredos.

## Rotas validadas

| Rota final | Cenário | Dependências evitadas |
|---|---|---|
| `blocked` | identificador inválido | banco, RAG e LLM |
| `blocked` | pedido de dosagem | banco, RAG e LLM |
| `patient_not_found` | paciente inexistente | RAG e LLM |
| `insufficient_context` | nenhuma evidência suficiente | chamada efetiva à LLM no serviço real |
| `human_validation` | resposta fundamentada | nenhuma; segue para revisão humana |
| `provider_error` | provider indisponível | validação de resposta inexistente |

O critério de aceite exigia quatro caminhos; seis caminhos distintos foram
executados e registrados nos testes.

## Testes

- 82 testes processados na suíte completa;
- 77 testes aprovados;
- 5 integrações externas ignoradas por padrão;
- zero falhas e zero erros;
- 14 testes unitários dos nós;
- 6 testes das rotas do grafo compilado.

As integrações opcionais exigem ativação explícita porque acessam PostgreSQL,
Ollama ou Google AI. Esses serviços já foram validados em execuções reais nos
dias anteriores.

## Diagrama

- Fonte gerada pelo LangGraph: `docs/diagrams/langgraph_flow.mmd`;
- versão renderizável em Markdown: `docs/diagrams/langgraph_flow.md`;
- oito nós verificados automaticamente pelo gerador.

## Limites desta etapa

- A auditoria ainda permanece em memória; a persistência no PostgreSQL pertence
  ao Dia 11.
- A segurança atual é uma primeira camada baseada em padrões explícitos; regras
  de urgência, prompt injection e validação ampliada pertencem ao Dia 11.
- Toda resposta médica permanece sujeita à validação humana.

## Evidências

- `src/medassist/application/graph_state.py`
- `src/medassist/application/graph_nodes.py`
- `src/medassist/application/graph_workflow.py`
- `tests/unit/test_graph_nodes.py`
- `tests/unit/test_graph_workflow.py`
- `scripts/generate_graph_diagram.py`
- `docs/diagrams/langgraph_flow.mmd`
- `docs/diagrams/langgraph_flow.md`
