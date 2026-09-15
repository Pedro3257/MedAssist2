# Constituição do MedAssist

**Versão:** 1.0.0  
**Ratificada em:** 01/09/2026  
**Escopo:** Tech Challenge FIAP - Fase 3

Esta constituição define princípios não negociáveis para especificar, implementar e avaliar o MedAssist. Em caso de conflito, segurança clínica, privacidade e rastreabilidade prevalecem sobre conveniência e velocidade.

## 1. Segurança clínica e supervisão humana

- O sistema é acadêmico e de apoio à decisão; não substitui avaliação profissional.
- Prescrição, dosagem, diagnóstico definitivo e conduta clínica autônoma são proibidos.
- Sugestões clínicas devem ser apresentadas como informação de apoio e exigir validação humana explícita.
- Possíveis urgências devem gerar orientação segura para buscar atendimento, nunca uma tentativa de manejo autônomo.

## 2. Privacidade por projeto

- Somente dados sintéticos de pacientes podem ser versionados ou usados na demonstração.
- Dados enviados a providers remotos devem ser minimizados e não conter identificadores desnecessários.
- Segredos, tokens e chaves nunca podem aparecer no repositório, nos prompts persistidos ou nos logs.

## 3. Respostas fundamentadas e explicáveis

- Afirmações médicas devem ser apoiadas por contexto recuperado e fontes identificáveis.
- Quando não houver evidência suficiente, o sistema deve se abster ou declarar a limitação.
- Toda resposta deve distinguir evidência recuperada, inferência do modelo e recomendação de validação humana.

## 4. Rastreabilidade e auditoria

- Todo requisito obrigatório deve possuir identificador, critério de aceite e evidência planejada.
- Decisões relevantes devem ser registradas com data, motivação e consequências.
- Execuções do assistente devem registrar correlation ID, decisão, provider, modelo, fontes e latência, sem segredos.

## 5. Reprodutibilidade

- Preparação de dados, fine-tuning, ingestão vetorial, testes e avaliação devem ser executáveis por comandos documentados.
- Versões, seeds, configurações, métricas e hashes de artefatos devem ser preservados quando aplicável.
- Uma entrega só é concluída quando há especificação, implementação, verificação, evidência e documentação mínima.

## 6. Modularidade e independência de provider

- O código deve ser modularizado em Python, com domínio e casos de uso independentes de infraestrutura.
- Ollama e Google AI Studio devem implementar um contrato comum, sem alterar casos de uso.
- Fine-tuning e RAG são pipelines distintos, avaliados separadamente e em conjunto.

## 7. Escopo mínimo e evolução controlada

- O escopo congelado em `history/DAILY_SCHEDULE.md` é a referência do MVP.
- Funcionalidades fora do MVP exigem alteração explícita de requisitos, arquitetura, cronograma e rastreabilidade.
- A simplicidade demonstrável prevalece sobre componentes sem evidência de valor para os requisitos.

## Governança

1. Mudanças nesta constituição exigem justificativa registrada em `history/PROJECT_HISTORY.md`.
2. Alterações incompatíveis incrementam a versão principal; novos princípios, a secundária; esclarecimentos, a versão de correção.
3. Cada revisão deve conferir a conformidade dos requisitos, código, testes e evidências com estes princípios.

