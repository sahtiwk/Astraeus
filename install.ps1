param(
    [ValidateSet('Core', 'Search', 'Diagnosis')]
    [string]$Profile = 'Core',
    [switch]$ChooseProfile,
    [switch]$Offline
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not [Environment]::Is64BitOperatingSystem -or $env:PROCESSOR_ARCHITECTURE -eq 'ARM64') {
    throw 'This release supports Windows x64.'
}
if ($ChooseProfile) {
    Write-Host 'Astraeus first-time setup'
    Write-Host '1. Core log analysis'
    Write-Host '2. Core plus local history search'
    Write-Host '3. Search plus local AI diagnosis (model download about 1.28 GB)'
    $choice = Read-Host 'Choose 1, 2 or 3'
    switch ($choice) {
        '1' { $Profile = 'Core' }
        '2' { $Profile = 'Search' }
        '3' { $Profile = 'Diagnosis' }
        default { throw 'Choose 1, 2 or 3 and run setup again.' }
    }
}
if ($Offline -and $Profile -ne 'Core') {
    throw 'Offline repair restores cached dependencies only. Use online setup to prepare optional models first.'
}
Write-Host "Installing profile $Profile into $PSScriptRoot"
Write-Host 'Online setup downloads Python and packages into this folder. Keep this folder after installation.'
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.cache/uv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '.python'
$bootstrap = Join-Path $PSScriptRoot '.bootstrap'
$uv = Join-Path $bootstrap 'uv.exe'
$archive = Join-Path $bootstrap 'uv-windows.zip'
$archiveHash = '529e78a9cec6cd7e3e014f7ecd8bda0c113969d4ed0f2efeedb85c30943325b8'
New-Item -ItemType Directory -Force $bootstrap | Out-Null
if (-not (Test-Path -LiteralPath $archive)) {
    if ($Offline) { throw 'Cached bootstrap archive missing. Run online setup once.' }
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -UseBasicParsing -Uri 'https://github.com/astral-sh/uv/releases/download/0.13.8/uv-x86_64-pc-windows-msvc.zip' -OutFile "$archive.partial"
    Move-Item -LiteralPath "$archive.partial" -Destination $archive -Force
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $archiveHash) {
    throw 'Bootstrap checksum mismatch. Remove .bootstrap/uv-windows.zip and retry setup.'
}
Expand-Archive -LiteralPath $archive -DestinationPath $bootstrap -Force
$syncArguments = @('sync', '--frozen', '--python', '3.11', '--no-dev', '--managed-python')
if ($Offline) { $syncArguments += '--offline' }
& $uv @syncArguments
if ($LASTEXITCODE -ne 0) { throw 'Package setup failed. Check internet access and available disk space, then run setup again.' }
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
& $uv pip check --python $python
if ($LASTEXITCODE -ne 0) { throw 'Dependency verification failed.' }
if ($Profile -in @('Search', 'Diagnosis')) {
    & $python -m scripts.prepare_embeddings --revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 --output models/embedding
    if ($LASTEXITCODE -ne 0) { throw 'Search model setup failed. Rerun setup to retry.' }
}
if ($Profile -eq 'Diagnosis') {
    & $python -m src.model_manager download
    if ($LASTEXITCODE -ne 0) { throw 'Diagnosis model setup failed. Rerun setup to resume.' }
    & $python -m src.model_manager runtime
    if ($LASTEXITCODE -ne 0) { throw 'Model runtime setup failed. Rerun setup to retry.' }
}
& $python -m src.installation_status
if ($LASTEXITCODE -ne 0) { throw 'Installation verification failed.' }
Write-Host 'Ready. Double-click Start Astraeus.cmd. Ctrl+C in the launcher stops the application.'
