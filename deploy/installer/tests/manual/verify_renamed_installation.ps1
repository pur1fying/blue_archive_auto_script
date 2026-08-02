param(
    [Parameter(Mandatory = $true)] [string]$SourcePath,
    [Parameter(Mandatory = $true)] [string]$TargetPath,
    [Parameter(Mandatory = $true)] [string]$InstallerPath
)

$ErrorActionPreference = 'Stop'
$source = [System.IO.Path]::GetFullPath($SourcePath).TrimEnd('\', '/')
$target = [System.IO.Path]::GetFullPath($TargetPath).TrimEnd('\', '/')
$installer = [System.IO.Path]::GetFullPath($InstallerPath)
$renamed = $target + '-renamed'
$parent = [System.IO.Path]::GetDirectoryName($target)
$targetLeaf = [System.IO.Path]::GetFileName($target)
$renamedLeaf = [System.IO.Path]::GetFileName($renamed)

if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw "Source does not exist: $source" }
if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) { throw "Installer does not exist: $installer" }
if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw "Target parent does not exist: $parent" }
if ($targetLeaf.Length -lt 8 -or $source -eq $target -or $source -eq $renamed) {
    throw 'Disposable target is not sufficiently specific or overlaps the source'
}
if ((Test-Path -LiteralPath $target) -or (Test-Path -LiteralPath $renamed)) {
    throw 'Both disposable target names must be unused'
}
if ($target.StartsWith($source + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase) -or
    $source.StartsWith($target + [System.IO.Path]::DirectorySeparatorChar,
        [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Disposable target and source must not contain one another'
}

function Assert-DisposablePath([string]$Path, [string]$ExpectedLeaf) {
    $resolved = [System.IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    if ([System.IO.Path]::GetDirectoryName($resolved) -ne $parent -or
        [System.IO.Path]::GetFileName($resolved) -ne $ExpectedLeaf) {
        throw "Refusing an operation outside the exact disposable target: $resolved"
    }
}

function Remove-DisposablePath([string]$Path, [string]$ExpectedLeaf) {
    Assert-DisposablePath $Path $ExpectedLeaf
    if (Test-Path -LiteralPath $Path) { Remove-Item -LiteralPath $Path -Recurse -Force }
}

try {
    New-Item -ItemType Directory -Path $target | Out-Null
    & robocopy.exe $source $target /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XD temp_clone /NFL /NDL /NJH /NJS /NP
    if ($LASTEXITCODE -ge 8) { throw "robocopy failed with exit code $LASTEXITCODE" }

    $targetInstaller = Join-Path $target 'BlueArchiveAutoScript.exe'
    Copy-Item -LiteralPath $installer -Destination $targetInstaller -Force
    $setup = Join-Path $target 'setup.toml'
    if (Test-Path -LiteralPath $setup) { Remove-Item -LiteralPath $setup -Force }
    $log = Join-Path $target 'log\installer.log'
    if (Test-Path -LiteralPath $log) { Remove-Item -LiteralPath $log -Force }
    $oldStamp = Join-Path $target '.baas-installer\dependencies-v1.sha256'
    if (Test-Path -LiteralPath $oldStamp) { Remove-Item -LiteralPath $oldStamp -Force }

    $process = Start-Process -FilePath $targetInstaller -ArgumentList '--auto-exit', '--no-launch' -PassThru
    $setupObserved = $false
    $networkObservedFirst = $false
    while (-not $process.HasExited) {
        if (Test-Path -LiteralPath $setup -PathType Leaf) { $setupObserved = $true }
        if (Test-Path -LiteralPath $log -PathType Leaf) {
            $currentLog = Get-Content -Raw -LiteralPath $log
            if ($currentLog -match 'Testing source|Receiving objects|Downloading package|Connecting to') {
                $networkObservedFirst = $true
                if (-not $setupObserved) { throw 'Network activity began before setup.toml was persisted' }
            }
        }
        Start-Sleep -Milliseconds 50
        $process.Refresh()
    }
    if ($process.ExitCode -ne 0) { throw "First installer run failed with exit code $($process.ExitCode)" }
    if (-not $setupObserved -or -not (Test-Path -LiteralPath $setup -PathType Leaf)) {
        throw 'setup.toml was not observed during the first installation'
    }

    $stamp = Join-Path $target '.baas-installer\dependencies-v1.sha256'
    if (-not (Test-Path -LiteralPath $stamp -PathType Leaf)) { throw 'Dependency stamp was not created' }
    Assert-DisposablePath $target $targetLeaf
    Rename-Item -LiteralPath $target -NewName $renamedLeaf

    $renamedInstaller = Join-Path $renamed 'BlueArchiveAutoScript.exe'
    $renamedLog = Join-Path $renamed 'log\installer.log'
    $logOffset = (Get-Item -LiteralPath $renamedLog).Length
    & $renamedInstaller --auto-exit --no-launch
    if ($LASTEXITCODE -ne 0) { throw "Renamed installer run failed with exit code $LASTEXITCODE" }

    $reader = $null
    $stream = [System.IO.File]::Open($renamedLog, 'Open', 'Read', 'ReadWrite')
    try {
        $stream.Position = $logOffset
        $reader = [System.IO.StreamReader]::new($stream)
        $secondLog = $reader.ReadToEnd()
    } finally {
        if ($reader) { $reader.Dispose() } else { $stream.Dispose() }
    }
    if ($secondLog -notmatch 'Dependency SHA unchanged; uv skipped') {
        throw 'Renamed run did not use the dependency SHA cache'
    }
    if ($secondLog -match 'Testing source|pip compile|pip sync') {
        throw 'Renamed cache-hit run unexpectedly benchmarked or resolved dependencies'
    }

    $pyvenv = Join-Path $renamed '.venv\pyvenv.cfg'
    $pyvenvText = Get-Content -Raw -LiteralPath $pyvenv
    $oldRootPattern = '(?i)' + [regex]::Escape($target) + '[\\/]'
    $staleKeys = @($pyvenvText -split "`r?`n" | Where-Object {
        $_ -match $oldRootPattern
    } | ForEach-Object { (($_ -split '=', 2)[0]).Trim() })
    if ($staleKeys.Count -gt 0) {
        throw "pyvenv.cfg retained the previous disposable root in fields: $($staleKeys -join ', ')"
    }
    $absoluteManagedPath = $pyvenvText -match '(?im)^\s*(home|executable|command)\s*=\s*([A-Za-z]:\\|/)'
    if ($absoluteManagedPath -and
        $pyvenvText.IndexOf($renamed, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
        throw 'An absolute managed pyvenv.cfg path was not repaired to the renamed root'
    }
    $python = Join-Path $renamed '.venv\Scripts\python.exe'
    $pythonReport = & $python -c 'import sys, cv2, numpy, requests; print(sys.prefix); print(sys.executable)'
    if ($LASTEXITCODE -ne 0) { throw 'Representative dependency imports failed after rename' }
    foreach ($line in $pythonReport) {
        if (-not [System.IO.Path]::GetFullPath($line).StartsWith($renamed, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Managed Python escaped the renamed installation root: $line"
        }
    }

    [pscustomobject]@{
        Source = $source
        RenamedTarget = $renamed
        SetupBeforeNetwork = $setupObserved -and (-not $networkObservedFirst -or $setupObserved)
        DependencyCacheHit = $true
        Python = $pythonReport[-1]
        Result = 'PASS'
    }
} finally {
    Remove-DisposablePath $target $targetLeaf
    Remove-DisposablePath $renamed $renamedLeaf
}
