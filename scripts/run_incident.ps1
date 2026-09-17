param (
    [string]$Scenario = "multi_source"
)

Write-Host "Triggering incident scenario: $Scenario" -ForegroundColor Cyan
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:8000/api/incidents/$Scenario/trigger" -Method Post
    $resp | ConvertTo-Json -Depth 4
} catch {
    Write-Host "Failed to connect to backend on http://localhost:8000. Is the server running?" -ForegroundColor Red
}
