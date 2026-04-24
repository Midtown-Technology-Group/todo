#!/usr/bin/env pwsh
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path $ScriptDir
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$SharedSrc = "C:\Users\ThomasBray\src\midtown-org-scan\microsoft-auth\src"
$TodoSrc = Join-Path $ProjectRoot "src"

if (Test-Path $VenvPython) {
    $env:PYTHONPATH = "$TodoSrc;$SharedSrc;$env:PYTHONPATH"
    & $VenvPython -m todo_cli.cli @Arguments
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
& $Python -m todo_cli.cli @Arguments
exit $LASTEXITCODE

