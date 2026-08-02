param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $true)]
    [string]$Installer
)

$ErrorActionPreference = 'Stop'
$sourcePath = [System.IO.Path]::GetFullPath($Source).TrimEnd('\', '/')
$targetPath = [System.IO.Path]::GetFullPath($Target).TrimEnd('\', '/')
$installerPath = [System.IO.Path]::GetFullPath($Installer)

if (-not (Test-Path -LiteralPath $sourcePath -PathType Container)) {
    throw "Source installation does not exist: $sourcePath"
}
if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
    throw "Installer executable does not exist: $installerPath"
}
if (Test-Path -LiteralPath $targetPath) {
    throw "Target must be a new path; refusing to overwrite: $targetPath"
}
if ($targetPath.StartsWith($sourcePath + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Target must not be inside the source installation'
}

$sourceSetup = Join-Path $sourcePath 'setup.toml'
$sourceSetupHash = if (Test-Path -LiteralPath $sourceSetup) {
    (Get-FileHash -LiteralPath $sourceSetup -Algorithm SHA256).Hash
} else { '' }
$sourceMainHead = if (Test-Path -LiteralPath (Join-Path $sourcePath '.git')) {
    (& git.exe -C $sourcePath rev-parse HEAD 2>$null)
} else { '' }

New-Item -ItemType Directory -Path $targetPath | Out-Null
& robocopy.exe $sourcePath $targetPath /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XD temp_clone /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

$installedExe = Join-Path $targetPath 'BlueArchiveAutoScript.exe'
Copy-Item -LiteralPath $installerPath -Destination $installedExe -Force
& $installedExe --auto-exit
if ($LASTEXITCODE -ne 0) {
    throw "Installer failed with exit code $LASTEXITCODE; inspect the target installation log"
}

$ocr = Join-Path $targetPath 'core\ocr\baas_ocr_client\bin'
$python = Join-Path $targetPath '.venv\Scripts\python.exe'
$required = @(
    (Join-Path $targetPath 'main.py'),
    (Join-Path $targetPath 'setup.toml'),
    (Join-Path $targetPath 'toolkit\uv\uv.exe'),
    $python,
    (Join-Path $ocr '.baas-installer-managed.json')
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Required installed path is missing: $path" }
}

function Get-FetchFingerprint([string]$Repository) {
    $fetchHead = Join-Path $Repository '.git\FETCH_HEAD'
    if (-not (Test-Path -LiteralPath $fetchHead -PathType Leaf)) { return 'missing' }
    $item = Get-Item -LiteralPath $fetchHead
    return "$( (Get-FileHash -LiteralPath $fetchHead -Algorithm SHA256).Hash ):$($item.LastWriteTimeUtc.Ticks)"
}

$mainUsesGit = Test-Path -LiteralPath (Join-Path $targetPath '.git') -PathType Container
$ocrUsesGit = Test-Path -LiteralPath (Join-Path $ocr '.git') -PathType Container
$mainHead = if ($mainUsesGit) { & git.exe -C $targetPath rev-parse HEAD } else { '' }
$ocrHead = if ($ocrUsesGit) { & git.exe -C $ocr rev-parse HEAD } else { '' }
if ($mainUsesGit -and $mainHead -notmatch '^[0-9a-f]{40}$') {
    throw 'Main repository HEAD is invalid'
}
if ($ocrUsesGit -and $ocrHead -notmatch '^[0-9a-f]{40}$') {
    throw 'OCR repository HEAD is invalid'
}

$mainFetchBefore = if ($mainUsesGit) { Get-FetchFingerprint $targetPath } else { '' }
$ocrFetchBefore = if ($ocrUsesGit) { Get-FetchFingerprint $ocr } else { '' }
& $installedExe --auto-exit --no-launch
if ($LASTEXITCODE -ne 0) { throw 'No-op verification pass failed' }
if ($mainUsesGit -and (Get-FetchFingerprint $targetPath) -ne $mainFetchBefore) {
    throw 'Matching main HEAD unexpectedly fetched again'
}
if ($ocrUsesGit -and (Get-FetchFingerprint $ocr) -ne $ocrFetchBefore) {
    throw 'Matching OCR HEAD unexpectedly fetched again'
}

$pythonReport = & $python -c "import sys, cv2, numpy, requests; print(sys.prefix); print(sys.executable)"
if ($LASTEXITCODE -ne 0) { throw 'Managed Python dependency import failed' }
foreach ($line in $pythonReport) {
    if (-not [System.IO.Path]::GetFullPath($line).StartsWith($targetPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Managed Python escaped the installation root: $line"
    }
}

$setup = Get-Content -Raw -LiteralPath (Join-Path $targetPath 'setup.toml')
if ($setup -notmatch 'package_manager\s*=\s*"uv"' -or $setup -notmatch 'runtime_path\s*=\s*"default"' -or
    $setup -notmatch 'current_baas_sha\s*=\s*"[^\"]+"' -or
    $setup -notmatch 'current_baas_cpp_sha\s*=\s*"[^\"]+"') {
    throw 'setup.toml was not atomically migrated to the portable uv/version configuration'
}

$logPath = Join-Path $targetPath 'log\installer.log'
$log = Get-Content -Raw -LiteralPath $logPath
$mainBackend = if ($mainUsesGit) { 'git' } else { 'mirrorchyan' }
$ocrBackend = if ($ocrUsesGit) { 'git' } else { 'mirrorchyan' }
if ($log -notmatch "\[main\]\[$mainBackend\]" -or $log -notmatch "\[ocr\]\[$ocrBackend\]" -or
    $log -notmatch '\[uv\]\[uv\]') {
    throw 'Unified log does not contain repository and uv backend output'
}
if ($log -match '[⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏]') { throw 'Spinner artifacts leaked into the normalized log' }

if ($sourceSetupHash -and (Get-FileHash -LiteralPath $sourceSetup -Algorithm SHA256).Hash -ne $sourceSetupHash) {
    throw 'Source setup.toml changed during disposable migration'
}
if ($sourceMainHead -and (& git.exe -C $sourcePath rev-parse HEAD 2>$null) -ne $sourceMainHead) {
    throw 'Source repository HEAD changed during disposable migration'
}

$launched = @(Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine.IndexOf($targetPath, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -and
    $_.CommandLine -match 'window\.py'
}).Count -gt 0
if (-not $launched) { throw 'BAAS did not remain running after the installer exited' }

[pscustomobject]@{
    Target = $targetPath
    MainBackend = $mainBackend
    OcrBackend = $ocrBackend
    MainHead = $mainHead
    OcrHead = $ocrHead
    Python = $pythonReport[-1]
    LaunchObserved = $launched
    NoFetchPass = $true
    Result = 'PASS'
}
