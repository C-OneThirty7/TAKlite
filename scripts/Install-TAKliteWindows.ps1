#Requires -RunAsAdministrator
[CmdletBinding()]
param(
    [string]$BindIp,
    [string]$InterfaceAlias,
    [string[]]$AllowedRemoteAddress = @("LocalSubnet"),
    [ValidateSet("Preserve", "Recreate")][string]$EnvMode = "Preserve",
    [switch]$SkipFirewall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$BundleRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $BundleRoot "docker-compose.yml"
$EnvironmentPath = Join-Path $BundleRoot ".env"
$RuntimeRoot = Join-Path $BundleRoot "taklite"
$ProjectName = "taklite"

function New-TAKliteToken {
    $bytes = New-Object byte[] 24
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $rng.GetBytes($bytes)
    } finally {
        $rng.Dispose()
    }
    return [Convert]::ToBase64String($bytes).Replace("+", "").Replace("/", "").Replace("=", "")
}

function Test-DockerEngine {
    try {
        & docker version --format '{{.Server.Version}}' 2>$null | Out-Null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Get-DockerDesktopExecutable {
    return @(
        (Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\Docker Desktop.exe")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
}

function Initialize-DockerCliPath {
    if (Get-Command docker -ErrorAction SilentlyContinue) { return }

    $dockerCli = @(
        (Join-Path $env:ProgramFiles "Docker\Docker\resources\bin\docker.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\DockerDesktop\resources\bin\docker.exe")
    ) | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if ($dockerCli) {
        $env:Path = "$(Split-Path -Parent $dockerCli);$env:Path"
    }
}

function Start-DockerDesktopIfNeeded {
    if (Test-DockerEngine) { return }

    $dockerDesktop = Get-DockerDesktopExecutable
    if (-not $dockerDesktop) {
        throw "Docker Desktop was not found. Install Docker Desktop with the WSL 2 backend, start it once, then rerun this installer."
    }

    Write-Host "Starting Docker Desktop and waiting for its Linux engine..."
    Start-Process -FilePath $dockerDesktop | Out-Null
    $deadline = [DateTime]::UtcNow.AddMinutes(5)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-DockerEngine) { return }
        Start-Sleep -Seconds 5
    }
    throw "Docker Desktop's Linux engine did not become ready within five minutes."
}

function Test-UsableIPv4 {
    param([Parameter(Mandatory)][string]$Address)
    $parsed = [Net.IPAddress]::None
    if (-not [Net.IPAddress]::TryParse($Address, [ref]$parsed)) { return $false }
    if ($parsed.AddressFamily -ne [Net.Sockets.AddressFamily]::InterNetwork) { return $false }
    if ([Net.IPAddress]::IsLoopback($parsed) -or $parsed.Equals([Net.IPAddress]::Any)) { return $false }
    if ($Address -like "169.254.*") { return $false }
    return $true
}

function Select-TAKliteNetwork {
    $adapters = @(Get-NetAdapter -Physical | Where-Object {
        $_.Status -eq "Up" -and $_.PhysicalMediaType -notmatch "Bluetooth"
    })
    if ($adapters.Count -eq 0) {
        throw "No connected physical network adapter was detected."
    }

    $adapterDisplay = foreach ($adapter in $adapters) {
        $addresses = @(Get-NetIPAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { Test-UsableIPv4 -Address $_.IPAddress } |
            ForEach-Object { "$($_.IPAddress)/$($_.PrefixLength)" })
        [pscustomobject]@{
            Name = $adapter.Name
            InterfaceIndex = $adapter.InterfaceIndex
            IPv4 = $addresses -join ", "
            LinkSpeed = $adapter.LinkSpeed
        }
    }

    Write-Host ""
    Write-Host "Connected physical adapters:"
    $adapterDisplay | Format-Table -AutoSize | Out-Host

    if ([string]::IsNullOrWhiteSpace($InterfaceAlias)) {
        if (-not [string]::IsNullOrWhiteSpace($BindIp)) {
            $detectedByAddress = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
                Where-Object { $_.IPAddress -eq $BindIp } |
                ForEach-Object { $_.InterfaceIndex } |
                Select-Object -Unique)
            if ($detectedByAddress.Count -eq 1) {
                $detectedAdapter = $adapters | Where-Object InterfaceIndex -eq $detectedByAddress[0]
                if (@($detectedAdapter).Count -eq 1) {
                    $script:InterfaceAlias = $detectedAdapter.Name
                    Write-Host "Detected TAKlite address $BindIp on adapter '$InterfaceAlias'."
                }
            }
        }
        if ([string]::IsNullOrWhiteSpace($InterfaceAlias) -and $adapters.Count -eq 1) {
            $script:InterfaceAlias = $adapters[0].Name
            Write-Host "Selected the only connected physical adapter: '$InterfaceAlias'."
        }
        if ([string]::IsNullOrWhiteSpace($InterfaceAlias)) {
            $script:InterfaceAlias = Read-Host "Enter the exact adapter Name TAKlite should use"
        }
    }

    $selected = $adapters | Where-Object { $_.Name -eq $InterfaceAlias }
    if (@($selected).Count -ne 1) {
        throw "Exactly one connected physical adapter must match '$InterfaceAlias'."
    }

    $usable = @(Get-NetIPAddress -InterfaceIndex $selected.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { Test-UsableIPv4 -Address $_.IPAddress })
    if ($usable.Count -eq 0) {
        throw "Adapter '$InterfaceAlias' does not have a usable IPv4 address. Configure Windows networking first."
    }

    if ([string]::IsNullOrWhiteSpace($BindIp)) {
        if ($usable.Count -eq 1) {
            $script:BindIp = $usable[0].IPAddress
            Write-Host "Selected the adapter's IPv4 address: $BindIp/$($usable[0].PrefixLength)."
        } else {
            $script:BindIp = Read-Host "Enter the IPv4 address TAKlite should serve on"
        }
    }

    if (-not (Test-UsableIPv4 -Address $BindIp)) {
        throw "TAKlite requires a valid non-loopback IPv4 address."
    }
    $matching = @($usable | Where-Object { $_.IPAddress -eq $BindIp })
    if (-not $matching) {
        throw "Adapter '$InterfaceAlias' does not already own $BindIp. Configure it in Windows first, then rerun this installer."
    }

    Set-NetConnectionProfile -InterfaceIndex $selected.InterfaceIndex -NetworkCategory Private -ErrorAction SilentlyContinue | Out-Null
    return $selected
}

function Write-TAKliteEnvironment {
    if ((Test-Path -LiteralPath $EnvironmentPath -PathType Leaf) -and $EnvMode -eq "Preserve") {
        $envValues = Read-TAKliteEnvironment
        $envBindIp = if ($envValues.ContainsKey("WG_BIND_IP")) { $envValues["WG_BIND_IP"] } else { "" }
        if (-not (Test-UsableIPv4 -Address $envBindIp) -or $envBindIp -ne $BindIp) {
            throw "Existing .env is configured for WG_BIND_IP='$envBindIp', but this install selected '$BindIp'. Rerun with -EnvMode Recreate to regenerate Windows Docker settings."
        }
        Write-Host "Using existing .env for $envBindIp. Use -EnvMode Recreate to regenerate Windows Docker settings."
        return
    }

    New-Item -ItemType Directory -Force -Path `
        (Join-Path $RuntimeRoot "data"), `
        (Join-Path $RuntimeRoot "packages"), `
        (Join-Path $RuntimeRoot "certs") | Out-Null

    $bootstrapToken = New-TAKliteToken
    $lines = @(
        "WG_BIND_IP=$BindIp",
        "TAKLITE_PUBLIC_HOST=$BindIp",
        "TAKLITE_SERVER_HOST=$BindIp",
        "TAKLITE_CONTAINER_USER=10001:10001",
        "TAKLITE_AUTO_INIT_CERTS=true",
        "TAKLITE_ADMIN_TOKEN=$bootstrapToken",
        "TAKLITE_CERT_PASSWORD=atakatak",
        "TAKLITE_COT_HOST_PORT=58087",
        "TAKLITE_COT_TLS_HOST_PORT=8089",
        "TAKLITE_HTTP_HOST_PORT=8080",
        "TAKLITE_HTTPS_HOST_PORT=8443",
        "TAKLITE_WGDASHBOARD_URL=",
        "TAKLITE_MAX_UPLOAD_BYTES=268435456",
        "TAKLITE_COT_TLS_REQUIRE_CLIENT_CERT=true",
        "TAKLITE_ALLOW_LEGACY_CLIENT_CERT=false",
        "TAKLITE_ACCESS_CONTROL_ENFORCE=true",
        "TAKLITE_LEGACY_CERT_DOWNLOADS=false",
        "TAKLITE_SOCKET_SEND_TIMEOUT_SECONDS=2.5",
        "TAKLITE_GUI_UPDATE_ENABLED=false",
        "TAKLITE_GUI_UPDATE_COMMAND=",
        "TAKLITE_GUI_UPDATE_WORKDIR=",
        "TAKLITE_GUI_UPDATE_TIMEOUT_SECONDS=900",
        "TAKLITE_GUI_UPDATE_REQUEST_DIR=",
        "TAKLITE_SETTINGS_REQUEST_DIR=",
        "TAKLITE_FIREWALL_REQUEST_DIR=",
        "TAKLITE_WG_INTERFACE=",
        "TAKLITE_PUBLIC_INTERFACE=$InterfaceAlias",
        "TAKLITE_WIREGUARD_PORT=",
        "TAKLITE_WGDASHBOARD_PORT="
    )
    [IO.File]::WriteAllLines($EnvironmentPath, $lines, [Text.UTF8Encoding]::new($false))
    Write-Host "Wrote TAKlite Windows Docker environment to $EnvironmentPath"
}

function Read-TAKliteEnvironment {
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $EnvironmentPath) {
        if ($line -match "^\s*#" -or $line -notmatch "=") { continue }
        $parts = $line -split "=", 2
        $values[$parts[0]] = $parts[1]
    }
    return $values
}

function Configure-TAKliteFirewall {
    param()
    if ($SkipFirewall) {
        Write-Host "Skipping Windows Firewall rule creation."
        return
    }

    $envValues = Read-TAKliteEnvironment
    $httpPort = if ($envValues.ContainsKey("TAKLITE_HTTP_HOST_PORT")) { $envValues["TAKLITE_HTTP_HOST_PORT"] } else { "8080" }
    $httpsPort = if ($envValues.ContainsKey("TAKLITE_HTTPS_HOST_PORT")) { $envValues["TAKLITE_HTTPS_HOST_PORT"] } else { "8443" }
    $cotPort = if ($envValues.ContainsKey("TAKLITE_COT_HOST_PORT")) { $envValues["TAKLITE_COT_HOST_PORT"] } else { "58087" }
    $tlsCotPort = if ($envValues.ContainsKey("TAKLITE_COT_TLS_HOST_PORT")) { $envValues["TAKLITE_COT_TLS_HOST_PORT"] } else { "8089" }
    $tcpPorts = @(
        [int]$httpPort,
        [int]$httpsPort,
        [int]$cotPort,
        [int]$tlsCotPort
    ) | Select-Object -Unique

    Get-NetFirewallRule -Group "TAKlite" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    New-NetFirewallRule -DisplayName "TAKlite LAN Services" -Group "TAKlite" -Direction Inbound `
        -Action Allow -Protocol TCP -LocalPort $tcpPorts -LocalAddress $BindIp `
        -RemoteAddress $AllowedRemoteAddress -InterfaceAlias $InterfaceAlias -Profile Private | Out-Null
    Write-Host "Created Windows Firewall rule group 'TAKlite' for TCP ports $($tcpPorts -join ', ') on $BindIp."
}

function Invoke-TAKliteCompose {
    & docker compose --project-name $ProjectName --env-file $EnvironmentPath --file $ComposeFile config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "TAKlite Docker Compose configuration is invalid."
    }

    & docker compose --project-name $ProjectName --env-file $EnvironmentPath --file $ComposeFile up --detach --build
    if ($LASTEXITCODE -ne 0) {
        throw "TAKlite container failed to start."
    }
}

if (-not [Environment]::Is64BitOperatingSystem) {
    throw "TAKlite Windows Docker mode requires 64-bit Windows."
}

Initialize-DockerCliPath
Start-DockerDesktopIfNeeded
if ((Test-Path -LiteralPath $EnvironmentPath -PathType Leaf) -and $EnvMode -eq "Preserve" -and [string]::IsNullOrWhiteSpace($BindIp)) {
    $existingEnv = Read-TAKliteEnvironment
    if ($existingEnv.ContainsKey("WG_BIND_IP") -and (Test-UsableIPv4 -Address $existingEnv["WG_BIND_IP"])) {
        $BindIp = $existingEnv["WG_BIND_IP"]
        Write-Host "Existing .env requests TAKlite bind IP $BindIp."
    }
}
$selectedAdapter = Select-TAKliteNetwork
Write-TAKliteEnvironment
Configure-TAKliteFirewall
Invoke-TAKliteCompose

$envValues = Read-TAKliteEnvironment
$hostValue = $envValues["TAKLITE_PUBLIC_HOST"]
$httpPort = $envValues["TAKLITE_HTTP_HOST_PORT"]
$httpsPort = $envValues["TAKLITE_HTTPS_HOST_PORT"]
$cotPort = $envValues["TAKLITE_COT_HOST_PORT"]
$tlsCotPort = $envValues["TAKLITE_COT_TLS_HOST_PORT"]
$token = $envValues["TAKLITE_ADMIN_TOKEN"]

Write-Host ""
Write-Host "TAKlite Windows Docker mode is running."
Write-Host ""
Write-Host "Dashboard:       http://$hostValue`:$httpPort/"
Write-Host "User portal:     http://$hostValue`:$httpPort/connect/"
Write-Host "HTTPS/Marti:     https://$hostValue`:$httpsPort/Marti"
Write-Host "Plain CoT:       $hostValue`:$cotPort"
Write-Host "TLS CoT:         $hostValue`:$tlsCotPort"
Write-Host "Bootstrap token: $token"
Write-Host ""
Write-Host "WireGuard is optional in this mode and is not installed by TAKlite."
Write-Host "Use your existing VPN/networking path, or install/manage WireGuard separately if this Windows host needs VPN service."
