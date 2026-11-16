# One-time local setup for Windows 10/11 (PowerShell). Run from anywhere:
#   powershell -ExecutionPolicy Bypass -File .\infrastructure\scripts\setup-windows.ps1
$ErrorActionPreference = 'Stop'
$root = Resolve-Path (Join-Path $PSScriptRoot '..\..')
Set-Location $root

function Test-Tool($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "'$name' was not found on PATH. $hint"
    }
}

Test-Tool 'python' 'Install Python 3.12 from python.org (tick "Add python.exe to PATH").'
Test-Tool 'node' 'Install Node.js 22 LTS from nodejs.org.'
Test-Tool 'npm' 'Install Node.js 22 LTS from nodejs.org.'

$pyVersion = (python --version) 2>&1
Write-Host "Using $pyVersion"
if ($pyVersion -notmatch 'Python 3\.(1[2-9]|[2-9]\d)') {
    Write-Warning 'Python 3.12+ is required. Continuing, but installs may fail.'
}

# Backend virtual environment
$venv = Join-Path $root 'backend\.venv'
if (-not (Test-Path $venv)) {
    Write-Host 'Creating backend\.venv ...'
    python -m venv $venv
}
$venvPython = Join-Path $venv 'Scripts\python.exe'
& $venvPython -m pip install --upgrade pip
Push-Location (Join-Path $root 'backend')
& $venvPython -m pip install -r requirements-dev.txt
Pop-Location

# Frontend dependencies
Push-Location (Join-Path $root 'frontend')
npm ci
Pop-Location

# Environment file
$envFile = Join-Path $root '.env'
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root '.env.example') $envFile
    $secret = & (Join-Path $PSScriptRoot 'generate-secret.ps1')
    (Get-Content $envFile) -replace '^JWT_SECRET=.*$', "JWT_SECRET=$secret" | Set-Content $envFile
    Write-Host 'Created .env with a freshly generated JWT_SECRET. Edit DATABASE_URL as needed.'
} else {
    Write-Host '.env already exists; left unchanged.'
}

Write-Host ''
Write-Host 'Next steps:'
Write-Host '  1. Start Postgres (docker compose up -d db) or point DATABASE_URL in .env to Neon.'
Write-Host '  2. cd backend; .\.venv\Scripts\Activate.ps1; alembic upgrade head'
Write-Host '  3. uvicorn app.main:app --reload --port 8000'
Write-Host '  4. In a second terminal: cd frontend; npm run dev'
Write-Host 'See docs\setup-guide.md for details.'
