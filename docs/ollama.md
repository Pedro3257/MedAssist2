# Execução do MedAssist no Ollama

## Artefato

- Modelo-base: `llama3.2:1b`.
- Modelo local: `medassist-local:1.0.0`.
- Adapter: `medassist-llama32-1b-qlora-adapter-v1.0.0-f16.gguf`.
- SHA-256 do adapter GGUF: `4ef5939ec02b27cd2296b713e6ad2154189d108b61623a85a813ef2010e8f189`.
- Modelfile reproduzível: `configs/ollama/Modelfile`.

O adapter Safetensors foi convertido para GGUF F16 com o script oficial `convert_lora_to_gguf.py` do `llama.cpp`. A conversão foi necessária porque a importação direta do Safetensors no Ollama para Windows localizou os pesos, mas falhou ao resolver `adapter_config.json`.

## Pré-requisitos

- Ollama instalado e em execução;
- `llama3.2:1b` disponível localmente;
- adapter GGUF preservado em `models/medassist-local/1.0.0/ollama/`.

## Verificação do artefato

```powershell
# Calcula o SHA-256 local para confirmar que o adapter GGUF não foi alterado.

Get-FileHash `
    -Algorithm SHA256 `
    -LiteralPath '.\models\medassist-local\1.0.0\ollama\medassist-llama32-1b-qlora-adapter-v1.0.0-f16.gguf'
```

O valor deve ser igual ao hash registrado na seção Artefato.

## Criação do modelo

Execute na raiz do projeto:

```powershell
# Cria a versão local do MedAssist usando o modelo-base e o adapter GGUF.

ollama create medassist-local:1.0.0 `
    --file '.\configs\ollama\Modelfile'
```

Confirme o registro e a configuração:

```powershell
# Confirma que o modelo existe e exibe a configuração armazenada pelo Ollama.

ollama list
ollama show medassist-local:1.0.0 --modelfile
```

O `ADAPTER` exibido pelo Ollama deve referenciar o blob de hash `4ef5939ec02b27cd2296b713e6ad2154189d108b61623a85a813ef2010e8f189`.

## Smoke test

```powershell
# Confirma que o modelo customizado responde localmente a uma pergunta não usada no treino.

ollama run medassist-local:1.0.0 'What are the treatments for Kidney Stones in Adults?'
```

## Revisão de respostas em português

O modelo ajustado foi treinado em inglês. Quando uma pergunta em português gera uma resposta em outro idioma, o fluxo pode chamar `gemma3:4b` como revisor local. Essa etapa deve preservar o conteúdo factual e as fontes recuperadas, alterando somente idioma, fluência e terminologia. O modelo revisor não substitui o `medassist-local:1.0.0` nem autoriza acrescentar diagnóstico ou conduta.

O modelo é configurado por `OLLAMA_LANGUAGE_REWRITE_MODEL` e sua execução fica registrada na proveniência da resposta.
## Limitações

- O modelo é um artefato acadêmico experimental e não está aprovado para uso clínico.
- A avaliação qualitativa encontrou respostas incompletas e afirmações médicas imprecisas.
- A integração com o Ollama demonstra que o adapter é carregável, não que sua saída seja clinicamente segura.
- Toda resposta deve passar por validação humana.
- O RAG fornece evidências recuperadas para reduzir respostas sem fundamentação.
- O modelo foi treinado em inglês; suporte treinado em português permanece no backlog pós-MVP.
