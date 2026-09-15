# MedAssist

MVP acadêmico de um assistente de informação médica que combina fine-tuning, RAG, LangChain, LangGraph, PostgreSQL/pgvector, múltiplos providers de LLM e controles determinísticos de segurança.

> **Aviso:** o MedAssist é um protótipo educacional. Não é um dispositivo médico, não realiza diagnóstico, não prescreve tratamentos e não substitui a avaliação de um profissional de saúde habilitado.

## 1. Problema e escopo

Modelos de linguagem podem produzir respostas convincentes mesmo quando estão incompletas ou sem fundamentação. Em saúde, esse comportamento exige fontes rastreáveis, recusa de solicitações inadequadas, proteção de dados, auditoria e validação humana.

O MedAssist demonstra um fluxo que:

- recebe uma pergunta e o identificador de um paciente sintético;
- bloqueia prescrição, dosagem individualizada, diagnóstico definitivo e tentativas de manipular as instruções internas;
- identifica possíveis urgências antes de consultar banco, RAG ou LLM;
- recupera somente os registros associados ao paciente informado;
- pesquisa evidências médicas do MedQuAD por similaridade vetorial;
- produz resposta contextualizada com fontes ou se abstém quando o contexto é insuficiente;
- exige validação humana para toda resposta médica gerada;
- registra decisão, provider, modelo, fontes, eventos e latência para auditoria.

O projeto utiliza conteúdo público curado e registros fictícios. O MedQuAD é a fonte dos exemplos de treinamento e da base de conhecimento; todos os pacientes, atendimentos e exames do PostgreSQL são sintéticos.

### Fora do escopo

- uso assistencial ou decisão clínica autônoma;
- dados reais de pacientes ou integração com sistemas hospitalares;
- diagnóstico, prescrição ou recomendação individual de dose;
- comprovação de eficácia clínica ou aprovação regulatória;
- treinamento de um modelo fundacional do zero;
- interface web de produção, autenticação hospitalar ou implantação em nuvem.

## 2. Arquitetura

O código separa domínio, aplicação e infraestrutura. O LangGraph controla as rotas e interrupções; o LangChain compõe recuperação, prompt, provider e parser; o PostgreSQL mantém registros sintéticos, conhecimento vetorial e auditoria.

| Componente | Responsabilidade |
|---|---|
| `src/medassist/domain` | Entidades e validações independentes de framework. |
| `src/medassist/application` | Casos de uso, segurança, contexto, auditoria e nós do grafo. |
| `src/medassist/infrastructure` | Configuração e repositórios PostgreSQL. |
| `src/medassist/providers` | Contrato comum e adapters Ollama e Google AI. |
| `src/medassist/rag` | Embeddings, recuperação pgvector e composição LangChain. |
| `migrations` | Banco relacional, dados sintéticos, vetores e auditoria. |
| `scripts` | Preparação, ingestão, avaliação, demonstração e inicialização. |
| `notebooks` | Análise do MedQuAD e fine-tuning reproduzível. |
| `reports/evidence` | Evidências de dados, treinamento, avaliação e demonstração. |

Os diagramas foram consolidados para evitar representações redundantes. A [documentação visual](docs/diagrams.md) contém somente a visão estrutural e o fluxo seguro detalhado. Decisões e limites de dependência estão descritos em [`specs/architecture.md`](specs/architecture.md).

## 3. Instalação e configuração

### Pré-requisitos

- Windows com PowerShell, ou comandos equivalentes em outro sistema;
- Python 3.12;
- Docker Desktop ou Docker Engine com Docker Compose v2;
- Ollama em execução;
- Git;
- espaço para os modelos, o PostgreSQL e 17.429 embeddings.

O ambiente de referência possui uma NVIDIA GTX 1050 Ti. A inferência também pode usar CPU; latência e distribuição entre CPU/GPU dependem do hardware e do modelo.

Na raiz do repositório, crie o ambiente e instale as dependências:

```powershell
# Cria e ativa um ambiente Python isolado para a aplicação.
conda create --name medassist python=3.12 -y
conda activate medassist
```

```powershell
# Instala as dependências diretas com versões fixadas.
python -m pip install --requirement .\requirements.txt
```

`requirements-lock.txt` registra o ambiente local completo. As bibliotecas do treinamento no Kaggle estão em `requirements-training.txt` e não são necessárias para executar a aplicação.

Crie a configuração local:

```powershell
# Copia o exemplo seguro; o arquivo .env resultante não deve ser versionado.
Copy-Item .\.env.example .\.env
```

Defina uma senha local em `POSTGRES_PASSWORD`. O provider padrão é `ollama`; a chave `GEMINI_API_KEY` deve permanecer vazia quando o provider remoto não for usado. Flags de integração vêm desativadas para evitar tráfego e custo involuntários.

### Inicialização completa

Esta distribuição não depende do adapter de fine-tuning para funcionar: por
padrão ela usa `llama3.2:1b`, que o Ollama baixa automaticamente. O script
abaixo instala dependências, baixa os modelos, obtém o MedQuAD, cria os chunks,
gera embeddings e valida o ambiente. Execute-o uma única vez (a geração dos
embeddings pode demorar):

```powershell
.\scripts\setup_medassist.ps1 -PostgresPassword (Read-Host 'Senha local do PostgreSQL' -AsSecureString)
```

Para executar usando o modelo ajustado, obtenha separadamente o adapter GGUF,
coloque-o no caminho documentado em `docs/ollama.md`, crie o modelo com Ollama
e mude `OLLAMA_MODEL` no `.env` para `medassist-local:1.0.0`.

Baixe os modelos exigidos pelo fluxo local:

```powershell
# Baixa a base, embeddings e o revisor de respostas em português.
ollama pull llama3.2:1b
ollama pull embeddinggemma:300m
ollama pull gemma3:4b
```

Com o adapter GGUF disponível no caminho documentado, registre o modelo ajustado:

```powershell
# Combina o Llama 3.2 1B com o adapter QLoRA convertido para GGUF.
ollama create medassist-local:1.0.0 --file .\configs\ollama\Modelfile
```

O procedimento e o hash esperado estão em [`docs/ollama.md`](docs/ollama.md).

## 4. PostgreSQL e pgvector

A imagem `pgvector/pgvector:pg16` mantém dados relacionais, documentos, embeddings e auditoria em um único serviço.

| Estrutura | Conteúdo |
|---|---|
| `patients`, `encounters`, `exams`, `pending_exams` | Registros exclusivamente sintéticos. |
| `knowledge_documents` | Coleção, fonte, URL e metadados do MedQuAD. |
| `knowledge_chunks` | Trechos recuperáveis e embeddings de 768 dimensões. |
| `audit_events` e tabelas relacionadas | Decisão, correlation ID, provider, modelo, fontes e eventos. |

As migrations são aplicadas em ordem na primeira criação do volume:

1. estrutura clínica sintética;
2. carga dos registros fictícios;
3. extensão `vector`;
4. documentos, chunks e embeddings;
5. índice HNSW;
6. auditoria.

```powershell
# Inicia o PostgreSQL e mostra sua condição de saúde.
docker compose up -d postgres
docker compose ps
```

A base validada contém 12 pacientes sintéticos, 5.479 documentos e 17.429 chunks vetorizados. Migrations executadas por `docker-entrypoint-initdb.d` não são reaplicadas em volumes existentes.

```powershell
# Encerra o container preservando o volume e os dados.
docker compose down
```

O esquema, as consultas de conferência e a política de dados sintéticos estão em [`docs/database.md`](docs/database.md).

## 5. Providers e modelos

Os casos de uso dependem do contrato `LLMProvider`, permitindo trocar a geração sem alterar a orquestração.

| Papel | Modelo/provider | Uso |
|---|---|---|
| Modelo-padrão | `llama3.2:1b` via Ollama | Execução local completa sem artefatos adicionais. |
| Modelo ajustado (opcional) | `medassist-local:1.0.0` via Ollama | Geração com adapter QLoRA, quando o GGUF estiver disponível. |
| Provider remoto | `gemini-3.6-flash` via Google AI | Alternativa de geração e teste de portabilidade. |
| Embeddings | `embeddinggemma:300m` via Ollama | Vetores multilíngues de 768 dimensões. |
| Revisor de idioma | `gemma3:4b` via Ollama | Reescreve em português quando a geração local diverge do idioma da pergunta, sem acrescentar fatos. |
| Avaliador automático | `qwen2.5:7b-instruct` via Ollama | LLM-as-a-Judge das 40 respostas selecionadas. |

O Gemma 3 não substitui o modelo ajustado: ele é acionado somente para corrigir o idioma da resposta e recebe as mesmas evidências como limite factual. O Qwen também não participa da resposta ao usuário; ele atribui notas e marca possíveis alucinações na avaliação offline.

Os 40 julgamentos Qwen formam o conjunto qualitativo principal. Trinta e dois julgamentos obtidos com Gemini foram preservados para comparação complementar. Nenhum deles representa revisão clínica humana.

## 6. Dataset e preparação dos dados

O MedQuAD original reúne perguntas e respostas médicas em XML, organizadas por tema (`Focus`) e pares (`QAPair`). O pipeline:

1. lê as coleções e registra problemas de qualidade;
2. remove pares sem pergunta ou resposta e coleções incompatíveis com o uso;
3. normaliza Unicode, espaços, entidades e HTML;
4. preserva coleção, fonte, URL, identificadores e metadados UMLS;
5. remove duplicatas de forma determinística;
6. cria JSONL curado e splits sem compartilhar o mesmo foco entre treino, validação e teste;
7. produz documentos e chunks separados para a base RAG.

Os splits usados no treinamento possuem 4.795 registros de treino, 603 de validação e 602 de teste. O conjunto de avaliação contém 40 casos médicos e 10 casos de segurança, com hash versionado para garantir repetibilidade.

Os principais pontos de entrada são:

- `notebooks/01_medquad_analysis.ipynb` — perfil e qualidade do dataset;
- `scripts/prepare_medquad.py` — curadoria;
- `scripts/split_medquad.py` — divisão determinística;
- `scripts/build_knowledge_chunks.py` — documentos e chunks do RAG;
- `scripts/ingest_knowledge_base.py` — embeddings e ingestão no pgvector.

O treinamento foi realizado em inglês. Um corpus médico em português e o treinamento multilíngue permanecem como melhoria futura.

## 7. Fine-tuning, RAG, LangChain e LangGraph

### Fine-tuning

O notebook `notebooks/02_finetuning.ipynb` aplica QLoRA ao `meta-llama/Llama-3.2-1B-Instruct`. Foram treinados 4.795 exemplos por uma época, em 600 passos, com validação separada e sem usar o conjunto de teste. O adapter foi convertido para GGUF F16 e incorporado ao modelo Ollama `medassist-local:1.0.0`.

O treinamento definitivo levou 43,38 minutos, atingiu `eval_loss` de 1,3219 e pico de 2,58 GB de VRAM no Kaggle com Tesla T4. Esses valores demonstram uma execução reproduzível, não eficácia clínica.

### RAG e LangChain

O `embeddinggemma:300m` transforma pergunta e chunks em vetores de 768 dimensões. O PostgreSQL/pgvector executa busca por similaridade e devolve texto, fonte, URL e pontuação. O LangChain combina o contexto sintético do paciente, as evidências recuperadas, o prompt e o parser da resposta. Sem evidência acima do limiar, o sistema se abstém antes de executar a LLM.

### LangGraph

O grafo coordena validação, segurança, consulta do paciente, recuperação, geração, validação da saída, revisão humana e auditoria. Há rotas explícitas para entrada inválida, bloqueio, urgência, paciente inexistente, contexto insuficiente, falha de provider e resposta fundamentada. Consulte o [fluxo consolidado](docs/diagrams.md#2-fluxo-seguro-do-langgraph).

## 8. Execução, testes, segurança e limitações

### Inicialização e execução

```powershell
# Inicia e valida banco, dependências, modelos Ollama e base vetorial.
.\scripts\start_medassist.ps1
```

```powershell
# Percorre o LangGraph completo para um paciente sintético.
python .\scripts\run_medassist_graph.py `
  PAT-001 `
  "What is autoimmune hemolytic anemia?" `
  --limit 3 `
  --minimum-similarity 0.55 `
  --max-tokens 384
```

```powershell
# Executa quatro rotas e salva demo-validacao-final-AAAAMMDD-HHMMSSmmm.txt.
.\scripts\run_demo.ps1 -Label "validacao-final"
```

### Testes

```powershell
# Executa todos os testes unitários sem chamar integrações externas.
$env:PYTHONPATH = "src"
python -m unittest discover -s tests\unit -v
```

```powershell
# Verifica se arquivos rastreados contêm chaves ou valores do .env local.
python .\scripts\check_secrets.py
```

A suíte validada contém 151 testes unitários. Testes remotos são desativados por padrão e só devem ser habilitados conscientemente pelas flags do `.env`.

### Segurança e auditoria

- filtros determinísticos atuam antes e depois da geração;
- solicitações de diagnóstico, prescrição e dose são bloqueadas;
- possíveis urgências recebem orientação controlada;
- prompt injection básica é recusada;
- contexto remoto é minimizado;
- queries são parametrizadas e segredos são removidos dos logs;
- toda execução possui correlation ID e trilha de nós;
- toda resposta médica exige validação humana.

### Avaliação e limitações

Foram executados 50 casos em quatro cenários: modelo-base e ajustado, com e sem RAG. Na amostra qualitativa de dez respostas por cenário, o modelo ajustado com RAG obteve médias 4,60 em relevância, 4,40 em correção, 4,10 em completude e 4,70 em groundedness; uma resposta foi marcada com possível alucinação. A [análise final](reports/evaluation_final.md) apresenta tabelas, gráficos, casos negativos e a comparação parcial Qwen–Gemini.

Esses resultados são específicos do conjunto, prompts, modelos e hardware registrados. Métricas lexicais e avaliações por LLM não comprovam correção ou segurança clínica. O MedQuAD pode conter conteúdo desatualizado, o fine-tuning foi feito em inglês e o revisor de idioma pode alterar estilo ou terminologia. O projeto não foi validado com pacientes reais nem por profissionais de saúde.

### Documentação de referência

- [`specs/constitution.md`](specs/constitution.md) — princípios e restrições;
- [`specs/requirements.md`](specs/requirements.md) — requisitos verificáveis;
- [`specs/traceability.md`](specs/traceability.md) — implementação e evidências;
- [`docs/diagrams.md`](docs/diagrams.md) — visão estrutural e fluxo seguro;
- [`docs/demo_script.md`](docs/demo_script.md) — roteiro reproduzível;
- [`reports/evidence`](reports/evidence) — resultados e evidências brutas.
