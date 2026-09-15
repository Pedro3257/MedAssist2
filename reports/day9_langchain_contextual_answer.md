# Dia 9 — LangChain e resposta contextualizada

**Data:** 09/09/2026  
**Status:** concluído

## Resultado

O pipeline contextualizado integra dados estruturados do paciente sintético,
recuperação semântica no PostgreSQL/pgvector, composição do prompt e geração
por um provider selecionável entre Ollama e Google AI Studio.

O fluxo apresenta a resposta, as evidências recuperadas, as fontes, as
limitações e a exigência de validação humana. Quando nenhuma evidência supera
o limiar de similaridade, o sistema se abstém sem chamar a LLM.

## Componentes implementados

- consulta parametrizada do paciente, atendimentos, exames concluídos e exames
  pendentes no PostgreSQL;
- adapter `BaseRetriever` do LangChain sobre o retriever pgvector existente;
- composição delimitada do contexto do paciente e das evidências médicas;
- prompt de geração com regras de segurança, idioma e fundamentação;
- serviço de resposta contextualizada com saída estruturada e proveniência;
- fallback determinístico por insuficiência de evidências;
- revisão opcional de idioma separada por provider;
- script executável para validar o fluxo completo.

## Validação real

### Ollama

- Modelo principal: `medassist-local:1.0.0`.
- Modelo revisor de idioma: `gemma3:4b`.
- Pergunta em português sobre pedras nos rins respondida em português após uma
  revisão de idioma.
- Duas evidências do NIDDK recuperadas e apresentadas.
- Consulta sem evidência suficiente produziu abstenção sem executar a LLM.

### Google AI Studio

- Provider: `google_ai`.
- Modelo: `gemini-3.6-flash`.
- Resposta gerada diretamente em português, sem revisão adicional de idioma.
- Duas evidências do NIDDK recuperadas, citadas no texto e apresentadas na
  proveniência.
- O texto distinguiu corretamente os dados do paciente sintético das
  informações médicas gerais.

## Testes automatizados

Comando executado no ambiente Conda `medassist`:

```powershell
# Executa todos os testes unitários e de integração configurados no projeto.
$env:PYTHONPATH = (Resolve-Path ".\src").Path
conda run -n medassist python -m unittest discover -s tests -p "test_*.py" -v
```

Resultado final:

- 62 testes processados;
- 57 testes aprovados;
- 5 integrações externas ignoradas por padrão;
- zero falhas e zero erros.

As integrações ignoradas exigem variáveis de ativação explícitas para consumir
Ollama, PostgreSQL ou Google AI. Os mesmos serviços foram validados manualmente
durante os Dias 8 e 9.

## Limitações observadas

- O MedQuAD está majoritariamente em inglês; a resposta em português pode
  exigir uma segunda chamada de revisão quando o modelo local é utilizado.
- A revisão automática pode introduzir imprecisões terminológicas. Em um teste,
  `nefrolitotomia percutânea` apareceu grafada incorretamente, reforçando a
  necessidade de validação humana.
- Similaridade vetorial não substitui avaliação clínica nem comprova que o
  paciente possui a condição descrita nas evidências.
- O contexto utiliza exclusivamente o paciente sintético `PAT-001`.

## Evidências de implementação

- `src/medassist/application/patient_context.py`
- `src/medassist/application/context_builder.py`
- `src/medassist/application/generation_prompt.py`
- `src/medassist/application/contextual_answer.py`
- `src/medassist/infrastructure/postgres_patient_repository.py`
- `src/medassist/infrastructure/langchain_retriever.py`
- `src/medassist/providers/factory.py`
- `scripts/show_patient_context.py`
- `scripts/search_knowledge_base_langchain.py`
- `scripts/build_generation_context.py`
- `scripts/run_contextual_answer.py`
- `tests/unit/test_contextual_answer.py`
- `tests/unit/test_contextual_answer_language.py`
- `tests/unit/test_provider_factory.py`
