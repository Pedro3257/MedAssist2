# Inicializa e valida os serviços locais necessários para executar o MedAssist.
# O script não imprime segredos, não baixa modelos e não altera a base existente.

[CmdletBinding()]
param(
    [switch]$SkipModelChecks,
    [switch]$SkipKnowledgeCheck
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot '.env'

function Get-EnvValue {
    param(
        [Parameter(Mandatory)]
        [string]$Name,
        [string]$Default = ''
    )

    if (Test-Path Env:$Name) {
        return (Get-Item Env:$Name).Value
    }

    if (Test-Path -LiteralPath $envFile) {
        $prefix = $Name + '='
        $line = Get-Content -Encoding UTF8 -LiteralPath $envFile |
            Where-Object {
                $_.Trim() -and
                -not $_.TrimStart().StartsWith('#') -and
                $_.StartsWith($prefix)
            } |
            Select-Object -Last 1

        if ($null -ne $line) {
            return $line.Substring($prefix.Length).Trim().Trim('"').Trim("'")
        }
    }

    return $Default
}

function Assert-Command {
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando obrigatório não encontrado: $Name"
    }
}

if (-not (Test-Path -LiteralPath $envFile)) {
    throw 'Arquivo .env ausente. Copie .env.example para .env e configure a senha.'
}

$postgresPassword = Get-EnvValue -Name 'POSTGRES_PASSWORD'

if (
    [string]::IsNullOrWhiteSpace($postgresPassword) -or
    $postgresPassword -eq 'change-me-local-only'
) {
    throw 'Defina uma senha local não padrão em POSTGRES_PASSWORD no arquivo .env.'
}

Assert-Command -Name 'docker'
Assert-Command -Name 'ollama'
Assert-Command -Name 'python'

Push-Location $projectRoot

try {
    $env:PYTHONPATH = Join-Path $projectRoot 'src'

    Write-Output 'Validando Docker Compose...'
    docker compose config --quiet

    Write-Output 'Iniciando PostgreSQL e pgvector...'
    docker compose up -d postgres

    $containerId = (docker compose ps -q postgres).Trim()

    if (-not $containerId) {
        throw 'O container PostgreSQL não foi criado.'
    }

    $healthy = $false

    for ($attempt = 1; $attempt -le 24; $attempt++) {
        $status = docker inspect `
            --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' `
            $containerId

        if ($status.Trim() -eq 'healthy') {
            $healthy = $true
            break
        }

        Start-Sleep -Seconds 2
    }

    if (-not $healthy) {
        throw 'O PostgreSQL não ficou saudável dentro do tempo esperado.'
    }

    Write-Output 'Validando dependências Python...'
    python -c "import langchain_core, langgraph, psycopg, pydantic, dotenv; print('Dependências Python: OK')"

    if ($LASTEXITCODE -ne 0) {
        throw 'A validação das dependências Python falhou. Confirme o ambiente medassist e instale requirements.txt.'
    }

    if (-not $SkipModelChecks) {
        Write-Output 'Validando Ollama e modelos locais...'
        $ollamaBaseUrl = Get-EnvValue `
            -Name 'OLLAMA_BASE_URL' `
            -Default 'http://127.0.0.1:11434'
        $tags = Invoke-RestMethod `
            -Method Get `
            -Uri ($ollamaBaseUrl.TrimEnd('/') + '/api/tags') `
            -TimeoutSec 15

        $availableModels = @($tags.models | ForEach-Object { $_.name })
        $requiredModels = @(
            (Get-EnvValue -Name 'OLLAMA_MODEL' -Default 'llama3.2:1b'),
            (Get-EnvValue -Name 'OLLAMA_EMBEDDING_MODEL' -Default 'embeddinggemma:300m'),
            (Get-EnvValue -Name 'OLLAMA_LANGUAGE_REWRITE_MODEL' -Default 'gemma3:4b')
        ) | Select-Object -Unique

        foreach ($model in $requiredModels) {
            if ($model -notin $availableModels) {
                throw "Modelo Ollama obrigatório não encontrado: $model"
            }
        }
    }

    if (-not $SkipKnowledgeCheck) {
        $postgresUser = Get-EnvValue -Name 'POSTGRES_USER' -Default 'medassist'
        $postgresDatabase = Get-EnvValue -Name 'POSTGRES_DB' -Default 'medassist'
        $chunkCount = docker compose exec -T postgres psql `
            -v ON_ERROR_STOP=1 `
            -U $postgresUser `
            -d $postgresDatabase `
            -tAc 'SELECT count(*) FROM knowledge_chunks WHERE embedding IS NOT NULL;'

        if ([int64]$chunkCount.Trim() -le 0) {
            throw 'A base vetorial está vazia. Execute scripts/ingest_knowledge_base.py.'
        }

        Write-Output ("Embeddings disponíveis: " + $chunkCount.Trim())
    }

    Write-Output 'MedAssist inicializado e validado com sucesso.'
    Write-Output 'Exemplo: python .\scripts\run_medassist_graph.py PAT-001 "What is autoimmune hemolytic anemia?"'
}
finally {
    Pop-Location
}
