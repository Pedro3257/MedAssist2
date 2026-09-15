# Dia 11 — Segurança e auditoria

**Data planejada:** 11/09/2026  
**Validação final:** 12/09/2026  
**Status:** concluído

## Resultado

O fluxo LangGraph passou a aplicar controles clínicos antes da consulta ao
paciente e da chamada à LLM, validar a saída gerada, exigir revisão humana e
persistir a decisão final no PostgreSQL com rastreabilidade. O envio ao provider
remoto usa uma cópia minimizada do contexto do paciente.

## Controles implementados

- bloqueio de prescrição, dosagem individualizada e diagnóstico definitivo;
- detecção de pedidos para substituir avaliação profissional;
- rota prioritária de urgência com orientação determinística para buscar ajuda;
- proteção básica contra tentativas de prompt injection;
- validação estruturada da resposta, das fontes e da proveniência;
- validação humana obrigatória nas rotas clínicas e controladas;
- minimização de nomes, identificadores e datas antes do provider remoto;
- redação de chaves Google, Bearer tokens, senhas e chaves privadas antes da
  persistência de perguntas, erros e eventos de auditoria.

## Auditoria no PostgreSQL

A migration `006_audit_events.sql` criou a tabela e os índices de consulta. Cada
execução registra correlation ID, timestamp, paciente sintético quando válido,
pergunta com eventuais segredos redigidos, decisão, provider, modelo, fontes,
latência, exigência de validação humana, código de erro e eventos do grafo.
Respostas completas não são armazenadas.

Duas execuções reais foram validadas. A solicitação de dosagem foi persistida
como `blocked`, sem fontes e sem chamada à LLM. A resposta fundamentada foi
persistida como `human_validation`, com provider, modelo, duas fontes e o
histórico dos nove nós do fluxo.

## Privacidade do provider remoto

Testes de fronteira confirmam que o Google AI recebe somente o contexto clínico
necessário: sexo biológico, motivos e notas clínicas, tipos e resultados de
exames e status de exames pendentes. Nome, ID do paciente, nascimento, IDs de
atendimentos/exames, datas exatas e textos administrativos de referência não
entram no prompt remoto. O fluxo local pode manter o contexto sintético completo.

## Validação de segredos

Na execução final, os arquivos pertencentes à estrutura oficial do projeto
foram verificados contra os valores sensíveis locais, sem achados. Diretórios
temporários de desenvolvimento permanecem fora do escopo das análises.

## Testes

- 127 testes processados;
- 122 testes aprovados;
- 5 integrações externas ignoradas por padrão;
- zero falhas e zero erros;
- testes específicos cobrem segurança clínica, prompt injection, validação de
  saída, auditoria, minimização remota e redação de segredos.

## Evidências

- `src/medassist/application/safety.py`
- `src/medassist/application/answer_validation.py`
- `src/medassist/application/privacy.py`
- `src/medassist/application/redaction.py`
- `src/medassist/application/audit.py`
- `src/medassist/application/graph_nodes.py`
- `src/medassist/application/graph_workflow.py`
- `src/medassist/infrastructure/postgres_audit_repository.py`
- `migrations/006_audit_events.sql`
- `scripts/run_medassist_graph.py`
- `scripts/check_secrets.py`
- `tests/unit/test_safety.py`
- `tests/unit/test_answer_validation.py`
- `tests/unit/test_graph_audit.py`
- `tests/unit/test_remote_context_flow.py`
- `tests/unit/test_redaction.py`
- `tests/unit/test_secret_safety.py`