#Requires -RunAsAdministrator
. "$PSScriptRoot\TAKliteWindowsCommon.ps1"

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$requestDir = Join-Path $script:RuntimeRoot "data\gui-update"
$statusPath = Join-Path $requestDir "status.json"
$requestPath = Join-Path $requestDir "request.json"
$processingPath = Join-Path $requestDir "processing.json"
$updateDir = Join-Path $script:BundleRoot "update"
$logPath = Join-Path $script:BundleRoot "taklite-admin\gui-update-last.log"

function Write-RunnerStatus {
    param(
        [Parameter(Mandatory)][string]$State,
        [Parameter(Mandatory)][string]$Message
    )
    New-Item -ItemType Directory -Path $requestDir -Force | Out-Null
    New-Item -ItemType Directory -Path (Split-Path -Parent $logPath) -Force | Out-Null
    $payload = [ordered]@{
        state = $State
        message = $Message
        updated_at = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
    }
    $payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statusPath -Encoding UTF8
}

function Test-VerifiedReleaseUrl {
    param([Parameter(Mandatory)][string]$Url)
    return $Url -match '^https://github\.com/C-OneThirty7/TAKlite/releases/download/v[0-9]+\.[0-9]+\.[0-9]+/[A-Za-z0-9_.-]+\.zip$'
}

function Invoke-QueuedUpdate {
    New-Item -ItemType Directory -Path $requestDir, $updateDir -Force | Out-Null
    if (-not (Test-Path -LiteralPath $requestPath -PathType Leaf)) { return }
    if (Test-Path -LiteralPath $processingPath -PathType Leaf) { return }

    Move-Item -LiteralPath $requestPath -Destination $processingPath -Force
    try {
        $request = Get-Content -LiteralPath $processingPath -Raw | ConvertFrom-Json
        $releaseZipUrl = [string]$request.release_zip_url
        $expectedSha256 = ([string]$request.expected_sha256).ToLowerInvariant()
        $targetTag = [string]$request.target_tag

        if (-not (Test-VerifiedReleaseUrl -Url $releaseZipUrl)) {
            throw "Invalid verified release zip URL."
        }
        if ($expectedSha256 -notmatch '^[a-f0-9]{64}$') {
            throw "Invalid release zip SHA-256."
        }

        Write-RunnerStatus "running" "Downloading $targetTag"
        $fileName = Split-Path -Leaf ([Uri]$releaseZipUrl).AbsolutePath
        $downloadPath = Join-Path $updateDir $fileName
        Invoke-WebRequest -Uri $releaseZipUrl -OutFile $downloadPath -UseBasicParsing

        $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $downloadPath).Hash.ToLowerInvariant()
        if ($actualHash -ne $expectedSha256) {
            Remove-Item -LiteralPath $downloadPath -Force -ErrorAction SilentlyContinue
            throw "Release zip SHA-256 mismatch."
        }

        Write-RunnerStatus "running" "Applying $targetTag"
        $output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "Update-TAKliteWindows.ps1") 2>&1
        $output | Set-Content -LiteralPath $logPath -Encoding UTF8
        if ($LASTEXITCODE -ne 0) {
            throw "TAKlite update failed. See $logPath"
        }
        Write-RunnerStatus "ok" "TAKlite update complete"
    } catch {
        Write-RunnerStatus "failed" $_.Exception.Message
        $_.Exception.Message | Add-Content -LiteralPath $logPath -Encoding UTF8
    } finally {
        Remove-Item -LiteralPath $processingPath -Force -ErrorAction SilentlyContinue
    }
}

Write-RunnerStatus "idle" "Windows GUI update runner started"
while ($true) {
    try {
        Invoke-QueuedUpdate
    } catch {
        Write-RunnerStatus "failed" $_.Exception.Message
    }
    Start-Sleep -Seconds 5
}
