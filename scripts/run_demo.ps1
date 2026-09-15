# Executa os casos oficiais de demonstração e salva uma transcrição auditável.
# Cada rota observada é comparada com a rota esperada antes de aprovar a execução.

[CmdletBinding()]
param(
    [Alias('Label')]
    [string]$RunLabel = 'execucao',
    [switch]$SkipStartup
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

if ($env:OS -eq 'Windows_NT') {
    & chcp.com 65001 | Out-Null
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$questionsPath = Join-Path $projectRoot 'configs\demo_questions.json'
$evidenceDirectory = Join-Path $projectRoot 'reports\evidence\demo'
$safeLabel = $RunLabel -replace '[^a-zA-Z0-9_-]', '-'
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmssfff'
$transcriptPath = Join-Path $evidenceDirectory (
    "demo-$safeLabel-$timestamp.txt"
)
$utf8WithoutBom = [System.Text.UTF8Encoding]::new($false)

function Write-DemoTranscript {
    param(
        [Parameter(Mandatory)]
        [AllowEmptyCollection()]
        [object[]]$Lines,
        [switch]$Append
    )

    $textLines = @(
        $Lines | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                $_.ToString()
            }
            else {
                [string]$_
            }
        }
    )

    foreach ($line in $textLines) {
        [Console]::WriteLine($line)
    }

    if ($Append) {
        [System.IO.File]::AppendAllLines(
            $transcriptPath,
            [string[]]$textLines,
            $utf8WithoutBom
        )
    }
    else {
        [System.IO.File]::WriteAllLines(
            $transcriptPath,
            [string[]]$textLines,
            $utf8WithoutBom
        )
    }
}

New-Item -ItemType Directory -Force -Path $evidenceDirectory | Out-Null
Push-Location $projectRoot

try {
    $env:PYTHONPATH = Join-Path $projectRoot 'src'
    $env:LLM_PROVIDER = 'ollama'

    if (-not $SkipStartup) {
        $previousErrorActionPreference = $ErrorActionPreference
        try {
            # Docker pode escrever mensagens normais em stderr mesmo com saída 0.
            $ErrorActionPreference = 'Continue'
            $startupResult = @(
                & (Join-Path $PSScriptRoot 'start_medassist.ps1')
            )
            $startupExitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
        Write-DemoTranscript -Lines $startupResult

        if ($null -ne $startupExitCode -and $startupExitCode -ne 0) {
            throw "A inicialização terminou com código $startupExitCode."
        }
    }
    else {
        Write-DemoTranscript -Lines @(
            'Inicialização automática ignorada por -SkipStartup.'
        )
    }

    $cases = Get-Content -Raw -Encoding UTF8 -LiteralPath $questionsPath |
        ConvertFrom-Json

    foreach ($case in $cases) {
        # Registra os dados completos do caso antes de executar o LangGraph.
        Write-DemoTranscript -Append -Lines @(
            ''
            ('=' * 80)
            ("CASO: " + $case.title)
            ("PACIENTE: " + $case.patient_id)
            ("PERGUNTA: " + $case.question)
            ("OBJETIVO: " + $case.purpose)
            ("ROTA ESPERADA: " + $case.expected_route)
            ('=' * 80)
        )

        $previousErrorActionPreference = $ErrorActionPreference
        try {
            # Bibliotecas nativas também podem emitir avisos válidos em stderr.
            $ErrorActionPreference = 'Continue'
            $result = @(
                python .\scripts\run_medassist_graph.py `
                    $case.patient_id `
                    $case.question `
                    --limit 2 `
                    --minimum-similarity 0.55 `
                    --max-tokens 384 2>&1
            )
            $exitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
        Write-DemoTranscript -Append -Lines $result

        if ($exitCode -ne 0) {
            throw "O caso $($case.id) terminou com código $exitCode."
        }

        $expectedText = "Rota final: $($case.expected_route)"
        if (($result -join "`n") -notmatch [regex]::Escape($expectedText)) {
            throw "O caso $($case.id) não percorreu a rota esperada."
        }
    }

    Write-DemoTranscript -Append -Lines @(
        ''
        ('=' * 80)
        ("DEMONSTRAÇÃO APROVADA: " + $cases.Count + " casos")
        ("TRANSCRIÇÃO: " + $transcriptPath)
        ('=' * 80)
    )
}
finally {
    Pop-Location
}