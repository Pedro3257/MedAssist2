# Preparação da release candidate

**Versão alvo:** `1.0.0-rc1`  
**Estado atual:** pronta para congelamento; ainda não etiquetada no Git.

## Evidências já validadas

- suíte final com 151 testes unitários aprovados, sem testes ignorados, em Python 3.12.14;
- quatro integrações locais aprovadas;
- integração remota final com Google AI aprovada em 14/09/2026: 1 teste em 1,285 s;
- migrations e recriação vetorial validadas em banco isolado;
- comando único de inicialização aprovado;
- duas demonstrações completas aprovadas, cada uma com quatro casos e quatro rotas esperadas;
- transcrições em `reports/evidence/demo/`, sem traceback, erro ou segredo detectado;
- scanner de segredos aprovado após a faxina, com 166 arquivos verificados;
- vídeo publicado e vinculado em `docs/RELATORIO_TECNICO.md`.

As duas transcrições finais foram gravadas em UTF-8, incluem as perguntas completas,
as quatro rotas observadas e não apresentam traceback ou erro de execução.

## Pendência para congelar a candidata

1. criar o commit-base e a tag da entrega após revisar o manifesto final.

## Geração do manifesto

Execute no ambiente `medassist`, a partir da raiz do projeto:

```powershell
# Valida os artefatos obrigatórios e gera suas assinaturas SHA-256.
python .\scripts\build_release_candidate.py
```

O resultado é salvo em
`reports/evidence/release_candidate_manifest.json`. Enquanto houver pendências,
o campo `status` permanece como `preparation`; isso evita tratar uma versão ainda
incompleta como candidata congelada.

## Regra de congelamento

Não criar a tag `v1.0.0-rc1` antes de todos os bloqueadores serem resolvidos. O
repositório também precisa possuir um commit-base rastreável para que a tag possa
identificar exatamente o código demonstrado.
