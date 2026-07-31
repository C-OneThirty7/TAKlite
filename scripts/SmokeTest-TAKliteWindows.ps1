. "$PSScriptRoot\TAKliteWindowsCommon.ps1"

Set-Location $script:BundleRoot
Initialize-TAKliteDockerCliPath
Start-TAKliteDockerDesktopIfNeeded

$envValues = Read-TAKliteEnvironment
if ($envValues.Count -eq 0) {
    throw "No TAKlite .env found in this folder. Run Install TAKlite first."
}

$hostValue = Get-TAKliteEnvValue $envValues "TAKLITE_PUBLIC_HOST" "127.0.0.1"
$httpPort = Get-TAKliteEnvValue $envValues "TAKLITE_HTTP_HOST_PORT" "8080"
$url = "http://$hostValue`:$httpPort/api/health"

Write-Host ""
Write-Host "Checking Docker container..."
& docker ps --filter "name=taklite" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
Write-Host ""

Write-Host "Checking TAKlite health:"
Write-Host "  $url"
try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
    Write-Host $response.Content
} catch {
    Write-Host "Health check failed: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "Recent TAKlite logs:"
& docker logs --tail 60 taklite 2>&1

Show-TAKliteSummary
