# Dia 13 — Testes e estabilização

**Data de início:** 12/09/2026  
**Estado:** execução parcial antecipada enquanto a avaliação qualitativa do Dia 12 aguarda renovação de cota.

## Testes unitários

- 146 testes executados.
- 146 testes aprovados.
- Nenhuma falha ou erro.
- O provider Google AI não foi chamado.

## Integrações locais

- Integração de geração com Ollama aprovada.
- Recuperação pgvector em inglês aprovada.
- Recuperação pgvector em português aprovada.
- Abstenção para pergunta não relacionada aprovada.
- Total: quatro testes aprovados em 76,415 segundos.
- A integração remota com Google AI permanece pendente; a avaliação do Dia 12 foi concluída com avaliador local e preservou 32 julgamentos Gemini como comparação complementar.

## Migrations em banco vazio

As migrations `001` a `006` foram aplicadas em ordem no banco isolado
`medassist_day13_test`, com interrupção imediata em caso de erro.

Validações:

- PostgreSQL criou todas as tabelas sem erro;
- pgvector 0.8.6 habilitado;
- 12 pacientes sintéticos carregados;
- tabela de chunks presente;
- tabela de auditoria presente.

## Recriação vetorial isolada

Foi executado um teste de fumaça com 10 chunks, evitando repetir a geração dos
17.429 embeddings apenas para testar o procedimento.

- 5.479 documentos carregados;
- 10 chunks inseridos;
- dimensões mínima e máxima iguais a 768;
- índice HNSW presente;
- distância de um vetor para ele mesmo igual a 0;
- banco temporário removido após a validação.

A base principal permaneceu intacta com 5.479 documentos, 17.429 chunks e 12
pacientes sintéticos.

## Caminhos e configuração

- 108 links relativos em Markdown verificados;
- nenhum link quebrado;
- Docker Compose validado;
- módulos em `src` e `scripts` compilados;
- caminhos absolutos do computador removidos dos dois relatórios JSON do MedQuAD;
- geradores ajustados para preferir caminhos relativos ao projeto.

## Configuração e inicialização

- `.env.example` revisado com todas as variáveis consumidas pela aplicação, valores locais seguros e integrações externas desativadas por padrão.
- `requirements.txt` registra cinco dependências diretas da aplicação com versões exatas.
- `requirements-training.txt` registra as seis bibliotecas do treinamento definitivo e a versão CUDA/PyTorch fornecida pelo Kaggle.
- `requirements-lock.txt` registra 45 pacotes diretos e transitivos do ambiente local Python 3.12.14.
- `pip check` não encontrou dependências incompatíveis.
- `scripts/start_medassist.ps1` valida `.env`, comandos, Docker Compose, saúde do PostgreSQL, imports Python, modelos Ollama e presença dos embeddings.
- A execução real do inicializador foi concluída com 17.429 embeddings disponíveis.
- Três testes unitários específicos do bootstrap foram aprovados.

## Demonstração preparada

- roteiro de 10 a 12 minutos criado em `docs/demo_script.md`;
- quatro perguntas oficiais versionadas em `configs/demo_questions.json`;
- dois casos fundamentados e dois bloqueios de segurança;
- executor `scripts/run_demo.ps1` salva transcrição e valida a rota de cada caso;
- CLI principal corrigida para execução direta sem `PYTHONPATH`;
- três novos testes aprovados; suíte completa com 146 testes unitários.

## Demonstração executada

- duas execuções completas registradas em `reports/evidence/demo/`;
- cada transcrição contém quatro casos e quatro rotas esperadas;
- ambas terminam com a aprovação dos quatro casos;
- nenhum traceback, marcador de erro ou padrão de segredo foi detectado;
- os arquivos foram gravados pelo PowerShell em UTF-16, sem prejuízo da evidência.

## Release candidate em preparação

- versão alvo definida como `1.0.0-rc1`;
- checklist criado em `docs/release_candidate.md`;
- configuração versionada em `configs/release_candidate.json`;
- gerador de manifesto criado em `scripts/build_release_candidate.py`;
- congelamento e tag permanecem bloqueados pela integração Google AI e pelos entregáveis acadêmicos finais.

## Pendências

- executar a integração remota com Google AI;
- concluir README, relatório, vídeo e rastreabilidade;
- congelar e etiquetar a release candidate somente depois dessas validações.