param([switch]$WithModel, [switch]$CoreOnly)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Double-click Install Astraeus.cmd first.' }
if ($WithModel -and $CoreOnly) { throw 'Choose WithModel or CoreOnly.' }
if ($WithModel) { & $python -m src.launcher --with-model }
elseif ($CoreOnly) { & $python -m src.launcher }
else { & $python -m src.launcher --auto-model }
exit $LASTEXITCODE
