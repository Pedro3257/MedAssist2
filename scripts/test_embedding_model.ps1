# Valida o modelo multilíngue de embeddings selecionado para o RAG.
# O teste confirma quantidade, dimensão e similaridade entre inglês e português.

$ErrorActionPreference = 'Stop'

$payload = @{
    model = 'embeddinggemma:300m'
    input = @(
        'What are the treatments for kidney stones?'
        'Quais são os tratamentos para cálculos renais?'
        'How is the weather today?'
    )
} | ConvertTo-Json -Depth 4

$response = Invoke-RestMethod `
    -Method Post `
    -Uri 'http://127.0.0.1:11434/api/embed' `
    -ContentType 'application/json' `
    -Body $payload

$embeddings = $response.embeddings

function Get-DotProduct {
    param(
        [Parameter(Mandatory)]
        $LeftVector,

        [Parameter(Mandatory)]
        $RightVector
    )

    $sum = 0.0

    for (
        $index = 0;
        $index -lt $LeftVector.Count;
        $index++
    ) {
        # Converte os dois elementos para números e acumula seu produto.
        $leftValue = [double]$LeftVector[$index]
        $rightValue = [double]$RightVector[$index]
        $sum += $leftValue * $rightValue
    }

    return $sum
}

$englishPortugueseSimilarity = Get-DotProduct `
    -LeftVector $embeddings[0] `
    -RightVector $embeddings[1]

$englishUnrelatedSimilarity = Get-DotProduct `
    -LeftVector $embeddings[0] `
    -RightVector $embeddings[2]

Write-Output (
    'Quantidade de vetores: ' + $embeddings.Count
)

Write-Output (
    'Dimensão: ' + $embeddings[0].Count
)

Write-Output (
    'Similaridade inglês/português: ' `
    + $englishPortugueseSimilarity
)

Write-Output (
    'Similaridade com frase não relacionada: ' `
    + $englishUnrelatedSimilarity
)

if ($embeddings.Count -ne 3) {
    throw 'Quantidade inesperada de vetores.'
}

if ($embeddings[0].Count -ne 768) {
    throw 'Dimensão inesperada para o EmbeddingGemma.'
}

if (
    $englishPortugueseSimilarity `
    -le $englishUnrelatedSimilarity
) {
    throw (
        'O teste multilíngue não apresentou ' `
        + 'a relação semântica esperada.'
    )
}

Write-Output 'Modelo multilíngue validado com sucesso.'
