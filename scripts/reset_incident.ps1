Write-Host "Resetting incident environment to clean default flagship scenario..." -ForegroundColor Cyan
try {
    $resp = Invoke-RestMethod -Uri "http://localhost:8000/api/incidents/reset" -Method Post
    $resp | ConvertTo-Json
} catch {
    Write-Host "Failed to connect to backend on http://localhost:8000. Is the server running?" -ForegroundColor Red
}
