<#
.SYNOPSIS
Builds the Windows CPU installer in one step.

.DESCRIPTION
Run on a 64-bit Windows PC from the repository root:

    powershell -ExecutionPolicy Bypass -File scripts\build_windows_installer.ps1

The result is dist\X-AnyLabeling-v<version>-Windows-CPU-Setup.exe.

Python 3.12 and Inno Setup 6.7.3 or later are required. If either is
missing, the script installs it with winget when winget is available.
Build dependencies go into a private virtual environment in
build\venv-windows, so other Python installations are not changed.

Use -Clean to delete that environment and the previous build first.
#>
param([switch]$Clean)

$ErrorActionPreference = 'Stop'
$rootDir = Split-Path $PSScriptRoot -Parent
Set-Location $rootDir

$minimumInnoVersion = [version]'6.7.3'
$venvDir = Join-Path $rootDir 'build\venv-windows'
$venvPython = Join-Path $venvDir 'Scripts\python.exe'
$spec = Join-Path $rootDir 'packaging\pyinstaller\specs\x-anylabeling-win-cpu.spec'

function Invoke-Checked {
    param([string]$File, [string[]]$Arguments)
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "'$File $($Arguments -join ' ')' failed with exit code $LASTEXITCODE."
    }
}

function Install-WithWinget {
    param([string]$Id, [string]$Name)
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "$Name is missing and winget is not available. Install $Name, then run this script again."
    }
    Write-Host "Installing $Name with winget..."
    & winget install --id $Id --exact --silent --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        throw "winget could not install $Name (exit code $LASTEXITCODE). Install it manually, then run this script again."
    }
}

function Find-Python312 {
    # py.exe reports a missing version on stderr; keep that from stopping the script.
    $previous = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        if (Get-Command py -ErrorAction SilentlyContinue) {
            $found = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $found) {
                return ($found | Select-Object -Last 1).Trim()
            }
        }
    } finally {
        $ErrorActionPreference = $previous
    }
    foreach ($candidate in @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:ProgramFiles 'Python312\python.exe')
    )) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

function Find-InnoCompiler {
    $command = Get-Command 'ISCC.exe' -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    foreach ($candidate in @(
        (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'),
        (Join-Path $env:ProgramFiles 'Inno Setup 6\ISCC.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
    )) {
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}

Write-Host '==> Checking Python 3.12'
$python = Find-Python312
if (-not $python) {
    Install-WithWinget -Id 'Python.Python.3.12' -Name 'Python 3.12'
    $python = Find-Python312
    if (-not $python) { throw 'Python 3.12 was installed but not found. Open a new PowerShell window and run this script again.' }
}
Write-Host "Using $python"

Write-Host '==> Checking Inno Setup'
$iscc = Find-InnoCompiler
if (-not $iscc) {
    Install-WithWinget -Id 'JRSoftware.InnoSetup' -Name 'Inno Setup 6'
    $iscc = Find-InnoCompiler
    if (-not $iscc) { throw 'Inno Setup was installed but ISCC.exe was not found. Open a new PowerShell window and run this script again.' }
}
$innoVersion = [version]((Get-Item $iscc).VersionInfo.ProductVersion -replace '[^0-9.].*$', '')
if ($innoVersion -lt $minimumInnoVersion) {
    throw "Inno Setup $innoVersion is too old; $minimumInnoVersion or later is required. Run: winget upgrade --id JRSoftware.InnoSetup"
}
Write-Host "Using $iscc ($innoVersion)"
# package_windows.ps1 finds the compiler through PATH.
$env:Path = "$(Split-Path $iscc -Parent);$env:Path"

if ($Clean) {
    Write-Host '==> Removing the previous build'
    foreach ($path in @($venvDir, (Join-Path $rootDir 'build\x-anylabeling-win-cpu'), (Join-Path $rootDir 'dist\X-AnyLabeling'))) {
        if (Test-Path $path) { Remove-Item -Recurse -Force $path }
    }
}

Write-Host '==> Installing build dependencies'
if (-not (Test-Path $venvPython)) {
    Invoke-Checked $python @('-m', 'venv', $venvDir)
}
Invoke-Checked $venvPython @('-m', 'pip', 'install', '--upgrade', 'pip')
Invoke-Checked $venvPython @('-m', 'pip', 'install', '-e', '.[cpu]', 'pyinstaller')

Write-Host '==> Building the application folder'
$env:X_ANYLABELING_PACKAGE_MODE = 'onedir'
$env:X_ANYLABELING_DEVICE = 'CPU'
Invoke-Checked $venvPython @('-m', 'PyInstaller', '--noconfirm', $spec)
$exe = Join-Path $rootDir 'dist\X-AnyLabeling\X-AnyLabeling.exe'
if (-not (Test-Path $exe)) { throw "PyInstaller finished but $exe is missing." }

Write-Host '==> Building the installer'
& (Join-Path $PSScriptRoot 'package_windows.ps1') -Variant CPU

$setup = Get-ChildItem (Join-Path $rootDir 'dist') -Filter 'X-AnyLabeling-v*-Windows-CPU-Setup.exe' |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host ''
Write-Host "Done: $($setup.FullName)"
Write-Host 'Copy this Setup.exe to the target PC and run it. No administrator rights are needed.'
