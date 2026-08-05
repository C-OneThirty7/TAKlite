Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:BundleRoot = Split-Path -Parent $PSScriptRoot
$script:ComposeFile = Join-Path $script:BundleRoot "docker-compose.yml"
$script:EnvironmentPath = Join-Path $script:BundleRoot ".env"
$script:RuntimeRoot = Join-Path $script:BundleRoot "taklite"
$script:OfflineImagePath = Join-Path $script:BundleRoot "images\taklite-offline.tar"
$script:OfflineImageName = "taklite-taklite:offline"
$script:ProjectName = "taklite"

function Initialize-TAKliteDockerCliPath {
    if (Get-Command docker -ErrorAction SilentlyContinue) { return }
    $dockerCli = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\resources\bin\docker.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if ($dockerCli) {
        $env:Path = "$(Split-Path -Parent $dockerCli);$env:Path"
    }
}

function Test-TAKliteDockerEngine {
    try {
        & docker version --format '{{.Server.Version}}' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-TAKliteDockerDesktopExecutable {
    return @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}

function Start-TAKliteDockerDesktopIfNeeded {
    if (Test-TAKliteDockerEngine) { return }
    $dockerDesktop = Get-TAKliteDockerDesktopExecutable
    if (-not $dockerDesktop) {
        throw "Docker Desktop was not found. Install Docker Desktop with the WSL 2 backend, start it once, then try again."
    }
    Write-Host "Starting Docker Desktop and waiting for its Linux engine..."
    Start-Process -FilePath $dockerDesktop | Out-Null
    $deadline = [DateTime]::UtcNow.AddMinutes(5)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-TAKliteDockerEngine) { return }
        Start-Sleep -Seconds 5
    }
    throw "Docker Desktop's Linux engine did not become ready within five minutes."
}

function Read-TAKliteEnvironment {
    $values = @{}
    if (-not (Test-Path -LiteralPath $script:EnvironmentPath -PathType Leaf)) {
        return $values
    }
    foreach ($line in Get-Content -LiteralPath $script:EnvironmentPath) {
        if ($line -match "^\s*#" -or $line -notmatch "=") { continue }
        $parts = $line -split "=", 2
        $values[$parts[0]] = $parts[1]
    }
    return $values
}

function Get-TAKliteEnvValue {
    param(
        [Parameter(Mandatory)][hashtable]$Values,
        [Parameter(Mandatory)][string]$Key,
        [string]$Default = ""
    )
    if ($Values.ContainsKey($Key)) { return $Values[$Key] }
    return $Default
}

function Invoke-TAKliteCompose {
    param([Parameter(Mandatory)][string[]]$ComposeArgs)
    $dockerArgs = @(
        "compose",
        "--project-name", $script:ProjectName,
        "--env-file", $script:EnvironmentPath,
        "--file", $script:ComposeFile
    ) + $ComposeArgs
    & docker @dockerArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose command failed: docker compose $($ComposeArgs -join ' ')"
    }
}

function Confirm-TAKliteAction {
    param(
        [Parameter(Mandatory)][string]$Title,
        [Parameter(Mandatory)][string]$Message
    )
    try {
        Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
        $result = [System.Windows.Forms.MessageBox]::Show(
            $Message,
            $Title,
            [System.Windows.Forms.MessageBoxButtons]::YesNo,
            [System.Windows.Forms.MessageBoxIcon]::Warning
        )
        return $result -eq [System.Windows.Forms.DialogResult]::Yes
    } catch {
        Write-Host ""
        Write-Host $Title
        Write-Host $Message
        $answer = Read-Host "Type YES to continue"
        return $answer -eq "YES"
    }
}

function Remove-TAKliteFirewallRules {
    try {
        Get-NetFirewallRule -Group "TAKlite" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
        Write-Host "Removed Windows Firewall rule group 'TAKlite' if it existed."
    } catch {
        Write-Host "Firewall cleanup warning: $($_.Exception.Message)"
    }
}

function Remove-TAKliteGuiUpdateRunner {
    try {
        Unregister-ScheduledTask -TaskName "TAKlite GUI Update Runner" -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Removed Windows GUI update runner scheduled task if it existed."
    } catch {
        Write-Host "GUI update runner cleanup warning: $($_.Exception.Message)"
    }
}

function Show-TAKliteSummary {
    $envValues = Read-TAKliteEnvironment
    $hostValue = Get-TAKliteEnvValue $envValues "TAKLITE_PUBLIC_HOST" "127.0.0.1"
    $httpPort = Get-TAKliteEnvValue $envValues "TAKLITE_HTTP_HOST_PORT" "8080"
    $httpsPort = Get-TAKliteEnvValue $envValues "TAKLITE_HTTPS_HOST_PORT" "8443"
    $cotPort = Get-TAKliteEnvValue $envValues "TAKLITE_COT_HOST_PORT" "58087"
    $tlsCotPort = Get-TAKliteEnvValue $envValues "TAKLITE_COT_TLS_HOST_PORT" "8089"
    $token = Get-TAKliteEnvValue $envValues "TAKLITE_ADMIN_TOKEN" ""

    Write-Host ""
    Write-Host "TAKlite paths:"
    Write-Host "  Folder:          $script:BundleRoot"
    Write-Host "  Environment:     $script:EnvironmentPath"
    Write-Host ""
    Write-Host "TAKlite URLs and ports:"
    Write-Host "  Dashboard:       http://$hostValue`:$httpPort/"
    Write-Host "  User portal:     http://$hostValue`:$httpPort/connect/"
    Write-Host "  HTTPS/Marti:     https://$hostValue`:$httpsPort/Marti"
    Write-Host "  Plain CoT:       $hostValue`:$cotPort"
    Write-Host "  TLS CoT:         $hostValue`:$tlsCotPort"
    if ($token) {
        Write-Host "  Bootstrap token: $token"
    }
    Write-Host ""
}
