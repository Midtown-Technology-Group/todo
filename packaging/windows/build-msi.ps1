param(
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$distDir = Join-Path $root "dist"
$buildDir = Join-Path $root "build"

if (Test-Path $distDir) {
    Remove-Item -Recurse -Force $distDir
}
if (Test-Path $buildDir) {
    Remove-Item -Recurse -Force $buildDir
}

python -m PyInstaller --clean --noconfirm (Join-Path $root "packaging\windows\todo.spec")

$env:PATH = "$env:USERPROFILE\.dotnet\tools;$env:PATH"
wix extension add WixToolset.Util.wixext
wix build `
    (Join-Path $root "packaging\windows\todo.wxs") `
    -ext WixToolset.Util.wixext `
    -d Version=$Version `
    -d BinDir=$distDir `
    -o (Join-Path $distDir "todo.msi")
