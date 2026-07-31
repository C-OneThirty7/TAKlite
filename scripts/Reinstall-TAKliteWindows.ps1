#Requires -RunAsAdministrator
. "$PSScriptRoot\TAKliteWindowsCommon.ps1"

Set-Location $script:BundleRoot
Initialize-TAKliteDockerCliPath
Start-TAKliteDockerDesktopIfNeeded

$ok = Confirm-TAKliteAction `
    -Title "Fresh Reinstall TAKlite" `
    -Message "This will wipe this folder's TAKlite .env, database, certificates, packages, and users, then run a fresh install with new credentials."
if (-not $ok) {
    Write-Host "Reinstall cancelled."
    exit 0
}

if (Test-Path -LiteralPath $script:EnvironmentPath -PathType Leaf) {
    try {
        Invoke-TAKliteCompose @("down", "--remove-orphans")
    } catch {
        Write-Host "Compose cleanup warning: $($_.Exception.Message)"
    }
}

try {
    & docker rm --force taklite 2>$null | Out-Null
} catch {}

Remove-TAKliteFirewallRules
Remove-Item -LiteralPath $script:EnvironmentPath -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $script:RuntimeRoot -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Starting fresh TAKlite install..."
& "$PSScriptRoot\Install-TAKliteWindows.ps1" -EnvMode Recreate
