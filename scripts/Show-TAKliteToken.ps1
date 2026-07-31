. "$PSScriptRoot\TAKliteWindowsCommon.ps1"

Set-Location $script:BundleRoot
Initialize-TAKliteDockerCliPath

$envValues = Read-TAKliteEnvironment
$token = Get-TAKliteEnvValue $envValues "TAKLITE_ADMIN_TOKEN" ""

if (-not $token) {
    try {
        if (Test-TAKliteDockerEngine) {
            $envLines = & docker inspect taklite --format '{{range .Config.Env}}{{println .}}{{end}}' 2>$null
            foreach ($line in $envLines) {
                if ($line -like "TAKLITE_ADMIN_TOKEN=*") {
                    $token = ($line -split "=", 2)[1]
                    break
                }
            }
        }
    } catch {
        $token = ""
    }
}

if (-not $token) {
    Write-Host ""
    Write-Host "TAKlite bootstrap token was not found."
    Write-Host ""
    Write-Host "Most common causes:"
    Write-Host "  - TAKlite was installed from a different extracted folder."
    Write-Host "  - Install did not complete."
    Write-Host "  - This folder was copied without its generated .env."
    Write-Host ""
    Write-Host "Run Install TAKlite again from the folder you want to use."
    Write-Host ""
    exit 1
}

try {
    Set-Clipboard -Value $token
    $copied = "yes"
} catch {
    $copied = "no"
}

Show-TAKliteSummary
Write-Host "Bootstrap token:"
Write-Host ""
Write-Host "  $token"
Write-Host ""
if ($copied -eq "yes") {
    Write-Host "The token has been copied to your clipboard."
}
Write-Host "Use this only for first admin setup. After the admin account exists, log in with that username and password."
Write-Host ""
