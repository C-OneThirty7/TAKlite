#Requires -RunAsAdministrator
. "$PSScriptRoot\TAKliteWindowsCommon.ps1"

Set-Location $script:BundleRoot
Initialize-TAKliteDockerCliPath
Start-TAKliteDockerDesktopIfNeeded

if (-not (Test-Path -LiteralPath $script:EnvironmentPath -PathType Leaf)) {
    throw "No TAKlite .env found in this folder. Run Install TAKlite first, or copy this new bundle over the existing TAKlite folder."
}

function Find-TAKliteBundleRoot {
    param([Parameter(Mandatory)][string]$ExtractRoot)
    $matches = @(Get-ChildItem -LiteralPath $ExtractRoot -Filter "docker-compose.yml" -Recurse -File |
        Where-Object {
            Test-Path -LiteralPath (Join-Path $_.DirectoryName "scripts\Update-TAKliteWindows.ps1") -PathType Leaf
        } |
        Select-Object -First 1)
    if ($matches.Count -ne 1) {
        throw "The update zip does not look like a TAKlite Windows bundle."
    }
    return $matches[0].DirectoryName
}

function Copy-TAKliteBundleFiles {
    param([Parameter(Mandatory)][string]$SourceRoot)
    $preserveNames = @(".env", "taklite", "taklite-admin", "update")
    foreach ($item in Get-ChildItem -LiteralPath $SourceRoot -Force) {
        if ($preserveNames -contains $item.Name) { continue }
        $destination = Join-Path $script:BundleRoot $item.Name
        Copy-Item -LiteralPath $item.FullName -Destination $destination -Recurse -Force
    }
}

function Load-TAKliteImage {
    param([Parameter(Mandatory)][string]$ImagePath)
    Write-Host "Loading TAKlite Docker image..."
    & docker load --input $ImagePath
    if ($LASTEXITCODE -ne 0) {
        throw "TAKlite offline Docker image failed to load."
    }
}

$updateDir = Join-Path $script:BundleRoot "update"
New-Item -ItemType Directory -Path $updateDir -Force | Out-Null
$updateZip = Get-ChildItem -LiteralPath $updateDir -Filter "*.zip" -File -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($updateZip) {
    Write-Host "Found update zip: $($updateZip.FullName)"
    $stage = Join-Path ([IO.Path]::GetTempPath()) ("taklite-update-" + [Guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    try {
        Write-Host "Extracting update zip..."
        Expand-Archive -LiteralPath $updateZip.FullName -DestinationPath $stage -Force
        $sourceRoot = Find-TAKliteBundleRoot -ExtractRoot $stage
        $sourceImage = Join-Path $sourceRoot "images\taklite-offline.tar"
        if (Test-Path -LiteralPath $sourceImage -PathType Leaf) {
            Load-TAKliteImage -ImagePath $sourceImage
        } else {
            Write-Host "No offline image was found inside the update zip. Existing/local image will be used."
        }
        Write-Host "Copying updated TAKlite files while preserving local data..."
        Copy-TAKliteBundleFiles -SourceRoot $sourceRoot
    } finally {
        Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    }
} elseif (Test-Path -LiteralPath $script:OfflineImagePath -PathType Leaf) {
    Load-TAKliteImage -ImagePath $script:OfflineImagePath
} else {
    Write-Host "No update zip or bundled offline image found. Docker will use the currently available TAKlite image."
}

Write-Host "Applying TAKlite update while preserving .env, users, certs, packages, and database..."
Invoke-TAKliteCompose @("up", "--detach", "--no-build")

Show-TAKliteSummary
Write-Host "TAKlite update completed."
