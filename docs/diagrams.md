# Diagramas do MedAssist

Este documento centraliza somente as duas visualizações necessárias para compreender o sistema. A primeira mostra responsabilidades e integrações; a segunda detalha as decisões executadas em uma requisição. Gráficos de resultados permanecem junto ao relatório de avaliação.

## 1. Visão estrutural

O diagrama separa entradas, orquestração, dados e modelos. O Qwen aparece fora do caminho de atendimento porque atua somente na avaliação offline.

```mermaid
%% Mostra os componentes e separa execução online de avaliação offline.
flowchart LR
    U[Usuário] --> CLI[CLI MedAssist]
    CLI --> G[LangGraph]
    G --> S[Segurança e validação]
    G --> LC[LangChain]
    G --> DB[(PostgreSQL)]
    DB --> PV[(pgvector + MedQuAD)]
    DB --> PC[(Pacientes sintéticos)]
    DB --> AU[(Auditoria)]
    LC --> LP[Contrato LLMProvider]
    LP --> OM[MedAssist ajustado / Ollama]
    LP --> GA[Google AI]
    OM --> GR[Gemma 3 revisor de idioma]
    EV[Resultados de quatro cenários] -. avaliação offline .-> QW[Qwen LLM-as-a-Judge]
```

## 2. Fluxo seguro do LangGraph

Cada saída passa por uma decisão explícita. Rotas interrompidas seguem diretamente para auditoria; somente uma resposta fundamentada chega à validação humana obrigatória.

```mermaid
%% Resume as rotas de sucesso, abstenção, bloqueio e falha controlada.
flowchart TD
    I[Validar entrada] -->|inválida| B[Resposta controlada]
    I --> S{Política de segurança}
    S -->|bloqueada| B
    S -->|possível urgência| U[Orientação de urgência]
    S -->|permitida| P{Paciente existe?}
    P -->|não| N[Paciente não encontrado]
    P -->|sim| C[Montar contexto sintético]
    C --> R[Recuperar evidências pgvector]
    R -->|insuficientes| X[Abstenção]
    R -->|suficientes| L[Gerar via LangChain e LLMProvider]
    L -->|falha| E[Erro controlado do provider]
    L --> V{Validar saída}
    V -->|inválida| B
    V -->|válida| H[Validação humana obrigatória]
    B --> A[Auditoria]
    U --> A
    N --> A
    X --> A
    E --> A
    H --> A
```
