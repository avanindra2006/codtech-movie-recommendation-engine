param([switch]$Development)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try {
    if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Python 3.13 is required.' }
    }
    $installTarget = if ($Development) { '.[dev,analysis]' } else { '.' }
    & .\.venv\Scripts\python.exe -m pip install -e $installTarget -c constraints.txt
    if ($LASTEXITCODE -ne 0) { throw 'Python package installation failed.' }
    if (-not (Test-Path -LiteralPath 'artifacts\model\config.json')) {
        & .\.venv\Scripts\cinematch.exe train
        if ($LASTEXITCODE -ne 0) { throw 'Model training failed.' }
    }
    Push-Location frontend
    try {
        npm.cmd ci --no-audit --no-fund
        if ($LASTEXITCODE -ne 0) { throw 'Frontend package installation failed.' }
        npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
    Write-Host 'Ready. Run: .\.venv\Scripts\cinematch.exe serve'
    Write-Host 'Then open http://127.0.0.1:8000'
} finally { Pop-Location }
