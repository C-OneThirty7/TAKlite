#Requires -RunAsAdministrator
. "$PSScriptRoot\TAKliteWindowsCommon.ps1"

Set-Location $script:BundleRoot
Initialize-TAKliteDockerCliPath
Start-TAKliteDockerDesktopIfNeeded

$ok = Confirm-TAKliteAction `
    -Title "Uninstall TAKlite" `
    -Message "This will stop and remove the TAKlite Docker container and Windows Firewall rules. It will not delete user data unless you approve the second prompt."
if (-not $ok) {
    Write-Host "Uninstall cancelled."
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
Remove-TAKliteGuiUpdateRunner

$deleteData = Confirm-TAKliteAction `
    -Title "Delete TAKlite Data?" `
    -Message "Delete this folder's TAKlite .env, database, packages, and certificates? Choose No if you may want to preserve users or connection packages."
if ($deleteData) {
    Remove-Item -LiteralPath $script:EnvironmentPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $script:RuntimeRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Deleted local TAKlite runtime data from this folder."
} else {
    Write-Host "Preserved local TAKlite runtime data in this folder."
}

Write-Host ""
Write-Host "TAKlite uninstall completed."
