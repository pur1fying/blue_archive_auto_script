param(
    [Parameter(Mandatory = $true)]
    [string]$SecretFile,

    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $true)]
    [string]$Installer
)

$ErrorActionPreference = 'Stop'
$secretPath = [System.IO.Path]::GetFullPath($SecretFile)
$targetPath = [System.IO.Path]::GetFullPath($Target)
$installerPath = [System.IO.Path]::GetFullPath($Installer)
if (-not (Test-Path -LiteralPath $secretPath -PathType Leaf)) { throw 'Mirror test input is unavailable' }
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) { throw 'Installer executable is unavailable' }
if (Test-Path -LiteralPath $targetPath) { throw 'Mirror test target must be a new directory' }

$candidates = @(Get-Content -LiteralPath $secretPath | ForEach-Object {
    $candidate = $_.Trim()
    if (-not $candidate -or $candidate.StartsWith('#')) { return }
    if ($candidate -match '^[A-Za-z_][A-Za-z0-9_]*\s*=\s*(.+)$') { $candidate = $Matches[1].Trim() }
    $candidate.Trim('"', "'")
} | Where-Object { $_ } | Select-Object -Unique)

$chosen = $null
foreach ($candidate in $candidates) {
    try {
        $encoded = [Uri]::EscapeDataString($candidate)
        $uri = "https://mirrorchyan.com/api/resources/BAAS_repo/latest?channel=stable&current_version=&user_agent=BAAS_GUI&cdk=$encoded"
        $response = Invoke-RestMethod -Uri $uri -Method Get -TimeoutSec 15
        if ($response.code -eq 0) { $chosen = $candidate; break }
    } catch { }
}
if (-not $chosen) { throw 'No valid Mirror test credential was found' }

New-Item -ItemType Directory -Path $targetPath | Out-Null
$installedExe = Join-Path $targetPath 'BlueArchiveAutoScript.exe'
Copy-Item -LiteralPath $installerPath -Destination $installedExe
$escaped = $chosen.Replace('\', '\\').Replace('"', '\"')
$setupPath = Join-Path $targetPath 'setup.toml'
$setup = @"
schema_version = 2

[general]
mirrorc_cdk = "$escaped"
channel = "stable"
current_baas_sha = ""
current_baas_cpp_sha = ""
git_backend = "auto"

[python]
runtime_path = "default"
python_version = "3.9.0"
package_manager = "uv"
"@
[System.IO.File]::WriteAllText($setupPath, $setup, [System.Text.UTF8Encoding]::new($false))

$success = $false
try {
    & $installedExe --auto-exit --no-launch
    if ($LASTEXITCODE -ne 0) { throw 'Mirror full installation failed' }
    $firstSetup = Get-Content -Raw -LiteralPath $setupPath
    $mainVersion = [regex]::Match($firstSetup, 'current_baas_sha\s*=\s*"([^\"]+)"').Groups[1].Value
    $ocrVersion = [regex]::Match($firstSetup, 'current_baas_cpp_sha\s*=\s*"([^\"]+)"').Groups[1].Value
    if (-not $mainVersion -or -not $ocrVersion) { throw 'Mirror versions were not saved atomically' }
    if ((Test-Path -LiteralPath (Join-Path $targetPath '.git')) -or
        -not (Test-Path -LiteralPath (Join-Path $targetPath 'core\ocr\baas_ocr_client\bin\.git'))) {
        throw 'Main Mirror deployment or OCR Git fallback metadata is incorrect'
    }

    & $installedExe --auto-exit --no-launch
    if ($LASTEXITCODE -ne 0) { throw 'Mirror current-version verification failed' }
    $secondSetup = Get-Content -Raw -LiteralPath $setupPath
    $secondMainVersion = [regex]::Match($secondSetup, 'current_baas_sha\s*=\s*"([^\"]+)"').Groups[1].Value
    $secondOcrVersion = [regex]::Match($secondSetup, 'current_baas_cpp_sha\s*=\s*"([^\"]+)"').Groups[1].Value
    if ($secondMainVersion -ne $mainVersion -or $secondOcrVersion -ne $ocrVersion) {
        throw 'Mirror no-op changed recorded versions'
    }
    $log = Get-Content -Raw -LiteralPath (Join-Path $targetPath 'log\installer.log')
    if ($log.Contains($chosen) -or $log -notmatch '\[main\]\[mirrorchyan\]' -or
        $log -notmatch '\[ocr\]\[mirrorchyan\].*BAAS_Cpp_prebuild' -or
        $log -notmatch '\[ocr\]\[(git|git-cli|libgit2)\]' -or
        $log -notmatch 'Downloading package' -or $log -notmatch 'already current') {
        throw 'Mirror logging, redaction, or current-version behavior failed'
    }
    $success = $true
} finally {
    if (Test-Path -LiteralPath $setupPath) {
        $scrubbed = (Get-Content -Raw -LiteralPath $setupPath) -replace '(?m)^(mirrorc_cdk\s*=\s*)"[^\"]*"', '$1""'
        [System.IO.File]::WriteAllText($setupPath, $scrubbed, [System.Text.UTF8Encoding]::new($false))
    }
}

$leaked = $false
foreach ($path in @((Join-Path $targetPath 'log'), (Join-Path $targetPath 'tmp'), (Join-Path $targetPath '.baas-installer'))) {
    if (-not (Test-Path -LiteralPath $path)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $path -Recurse -File -ErrorAction SilentlyContinue) {
        if ((Get-Content -Raw -LiteralPath $file.FullName -ErrorAction SilentlyContinue).Contains($chosen)) {
            $leaked = $true
            break
        }
    }
}
if ($leaked) { throw 'Mirror credential leaked into installer logs or state' }

[pscustomobject]@{
    Main = 'PASS'
    OcrGitFallback = 'PASS'
    CurrentVersion = 'PASS'
    SecretScan = -not $leaked
    Result = if ($success) { 'PASS' } else { 'FAIL' }
}
