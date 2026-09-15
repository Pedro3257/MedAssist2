# Prepara uma instalacao local reproduzivel do MedAssist.
# Requer Python 3.12, Docker Desktop/Compose, Ollama e Git ja instalados.

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [SecureString]$PostgresPassword,
    [switch]$SkipDataset,
    [switch]$SkipPythonInstall
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot '.env'
$datasetPath = Join-Path $projectRoot 'data\raw\MedQuAD-master'
$processedPath = Join-Path $projectRoot 'data\processed\knowledge_chunks.jsonl'

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Comando obrigatorio nao encontrado: $Name"
    }
}

Assert-Command python
Assert-Command docker
Assert-Command ollama
if (-not $SkipDataset) { Assert-Command git }

Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath $envFile)) {
        Copy-Item '.env.example' $envFile
        $credential = [System.Net.NetworkCredential]::new('', $PostgresPassword)
        $plainPassword = $credential.Password
        if ([string]::IsNullOrWhiteSpace($plainPassword)) {
            throw 'POSTGRES_PASSWORD nao pode estar vazia.'
        }
        $envText = Get-Content -Raw -Encoding UTF8 $envFile
        $envText = $envText.Replace(
            'POSTGRES_PASSWORD=change-me-local-only',
            "POSTGRES_PASSWORD=$plainPassword"
        )
        Set-Content -LiteralPath $envFile -Value $envText -Encoding UTF8 -NoNewline
        $plainPassword = $null
    }

    if (-not $SkipPythonInstall) {
        python -m pip install --requirement .\requirements.txt
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias Python.' }
    }

    foreach ($model in @('llama3.2:1b', 'embeddinggemma:300m', 'gemma3:4b')) {
        ollama pull $model
        if ($LASTEXITCODE -ne 0) { throw "Falha ao baixar o modelo Ollama: $model" }
    }

    docker compose up -d postgres
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar PostgreSQL/pgvector.' }

    if (-not $SkipDataset) {
        if (-not (Test-Path -LiteralPath $datasetPath)) {
            git clone --depth 1 https://github.com/abachaa/MedQuAD.git $datasetPath
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao baixar o dataset MedQuAD.' }
        }

        if (-not (Test-Path -LiteralPath $processedPath)) {
            python .\scripts\prepare_medquad.py --dataset $datasetPath
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao preparar o MedQuAD.' }
            python .\scripts\build_knowledge_chunks.py
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar os chunks da base RAG.' }
        }

        python .\scripts\ingest_knowledge_base.py
        if ($LASTEXITCODE -ne 0) { throw 'Falha ao ingerir a base vetorial.' }
    }

    .\scripts\start_medassist.ps1
}
finally {
    Pop-Location
}
