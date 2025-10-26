# Run this in PowerShell (Windows) or pwsh (cross-platform)
$apiKey = $env:ANTHROPIC_API_KEY
if (-not $apiKey) {
    Write-Error "ANTHROPIC_API_KEY is not set in your environment."
    exit 1
}

$model = $env:CLAUDE_RUNTIME_MODEL  
$body = @{
    model = $model
    max_tokens = 10
    messages = @(
        @{
            role = "user"
            content = @(
                @{ type = "text"; text = "Name your model and say Hello." }
            )
        }
    )
} | ConvertTo-Json

$response = Invoke-WebRequest `
    -Uri "https://api.anthropic.com/v1/messages" `
    -Method POST `
    -Headers @{
        "x-api-key" = $apiKey
        "anthropic-version" = "2023-06-01"
        "content-type" = "application/json"
    } `
    -Body $body `
    -TimeoutSec 30

if ($response.StatusCode -eq 200) {
    Write-Host "✅ Success! Model responded:"
    Write-Host $response.Content
} else {
    Write-Error "❌ Failed. Status code: $($response.StatusCode)"
    Write-Host $response.Content
}
