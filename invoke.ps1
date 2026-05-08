#!/usr/bin/env pwsh
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path $ScriptDir
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SharedSrc = $env:MTG_SHARED_AUTH_SRC
if ([string]::IsNullOrWhiteSpace($SharedSrc)) {
    $SharedSrc = Join-Path (Split-Path -Parent $ProjectRoot) "mtg-microsoft-auth\src"
}
if (-not (Test-Path -LiteralPath $SharedSrc -PathType Container)) {
    Write-Error "Shared auth source directory not found at '$SharedSrc'. Set MTG_SHARED_AUTH_SRC to the mtg-microsoft-auth src directory."
    exit 1
}
$SharedSrc = (Resolve-Path -LiteralPath $SharedSrc).Path
$TodoSrc = Join-Path $ProjectRoot "src"

if (Test-Path $VenvPython) {
    $env:PYTHONPATH = "$TodoSrc;$SharedSrc;$env:PYTHONPATH"
    & $VenvPython -m todo @Arguments
    exit $LASTEXITCODE
}

$Python = (Get-Command py -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    $Python = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $Python) {
    Write-Error "Python not found."
    exit 1
}

$env:PYTHONPATH = "$TodoSrc;$SharedSrc;$env:PYTHONPATH"
& $Python -m todo @Arguments
exit $LASTEXITCODE
