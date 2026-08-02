param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $true)]
    [string]$Installer
)

$ErrorActionPreference = 'Stop'
$sourcePath = [System.IO.Path]::GetFullPath($Source)
$targetPath = [System.IO.Path]::GetFullPath($Target)
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

New-Item -ItemType Directory -Path $targetPath | Out-Null
& robocopy.exe $sourcePath $targetPath /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XD temp_clone /NFL /NDL /NJH /NJS /NP
if ($LASTEXITCODE -ge 8) {
    throw "robocopy failed with exit code $LASTEXITCODE"
}

$installedExe = Join-Path $targetPath 'BlueArchiveAutoScript.exe'
Copy-Item -LiteralPath $installerPath -Destination $installedExe -Force
& $installedExe --auto-exit
if ($LASTEXITCODE -ne 0) {
    throw "Installer failed with exit code $LASTEXITCODE; inspect $targetPath\log\installer.log"
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

$mainHead = & git.exe -C $targetPath rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $mainHead -notmatch '^[0-9a-f]{40}$') { throw 'Main repository HEAD is invalid' }
$ocrHead = & git.exe -C $ocr rev-parse HEAD
if ($LASTEXITCODE -ne 0 -or $ocrHead -notmatch '^[0-9a-f]{40}$') { throw 'OCR repository HEAD is invalid' }

$pythonReport = & $python -c "import sys, cv2, numpy, requests; print(sys.prefix); print(sys.executable)"
if ($LASTEXITCODE -ne 0) { throw 'Managed Python dependency import failed' }
foreach ($line in $pythonReport) {
    if (-not [System.IO.Path]::GetFullPath($line).StartsWith($targetPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Managed Python escaped the installation root: $line"
    }
}

$setup = Get-Content -Raw -LiteralPath (Join-Path $targetPath 'setup.toml')
if ($setup -notmatch 'package_manager\s*=\s*"uv"' -or $setup -notmatch 'runtime_path\s*=\s*"default"') {
    throw 'setup.toml was not migrated to the portable uv configuration'
}

[pscustomobject]@{
    Target = $targetPath
    MainHead = $mainHead
    OcrHead = $ocrHead
    Python = $pythonReport[-1]
    Result = 'PASS'
}
