#Requires -Version 5.1
<#
.SYNOPSIS
    Plug-and-play launcher for the AI-Powered Data Security & Compliance Agent.

.DESCRIPTION
    Run this from the folder that contains app.py. It:
      1. checks Python is installed,
      2. installs the Python dependencies,
      3. creates .env from .env.example on first run (then asks you to fill it in),
      4. makes sure you are signed in to Azure (the app authenticates via Azure CLI),
      5. launches the Streamlit app.

.EXAMPLE
    ./run.ps1
        First run: installs deps, creates .env, opens it for you to fill in, then exits.
        Fill in .env, then run ./run.ps1 again to start the app.

.EXAMPLE
    ./run.ps1 -SkipInstall
        Skip the dependency install (use when deps are already installed).
#>
[CmdletBinding()]
param(
    [switch]$SkipInstall,   # skip 'pip install -r requirements.txt'
    [switch]$Headless       # run Streamlit without auto-opening a browser
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "=== Data Security & Compliance Agent : setup & run ===" -ForegroundColor Cyan

# 1) Python present?
try {
    $pyVersion = (& python --version) 2>&1
    Write-Host "Python detected: $pyVersion"
} catch {
    Write-Host "Python is not installed or not on PATH." -ForegroundColor Red
    Write-Host "Install Python 3.11+ from https://www.python.org/downloads/ (tick 'Add to PATH'), then re-run ./run.ps1"
    exit 1
}

# 2) Install dependencies
if (-not $SkipInstall) {
    Write-Host "Installing dependencies from requirements.txt ..." -ForegroundColor Yellow
    & python -m pip install --upgrade pip
    & python -m pip install -r requirements.txt
    Write-Host "Dependencies installed." -ForegroundColor Green
} else {
    Write-Host "Skipping dependency install (-SkipInstall)."
}

# 3) Ensure .env exists (first-run bootstrap)
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ""
    Write-Host "Created a new .env from .env.example." -ForegroundColor Green
    Write-Host "Fill in your Foundry / Cosmos / Storage / Event Grid values, save the file," -ForegroundColor Green
    Write-Host "then run ./run.ps1 again to start the app." -ForegroundColor Green
    try { Start-Process notepad.exe ".env" } catch {}
    exit 0
}

# 4) Azure login (the app authenticates via Azure CLI / DefaultAzureCredential)
$signedIn = $false
try {
    $acct = (& az account show 2>$null | ConvertFrom-Json)
    if ($acct) { $signedIn = $true; Write-Host "Azure: signed in as $($acct.user.name)" }
} catch { }
if (-not $signedIn) {
    Write-Host "You are not signed in to Azure." -ForegroundColor Yellow
    $answer = Read-Host "Run 'az login' now? (Y/n)"
    if ($answer -ne 'n' -and $answer -ne 'N') {
        & az login | Out-Null
    } else {
        Write-Host "Continuing without login - the app will fail to reach the agents until you run 'az login'." -ForegroundColor Yellow
    }
}

# 5) Launch the app
Write-Host "Starting Streamlit (press Ctrl+C to stop) ..." -ForegroundColor Cyan
$streamlitArgs = @("run", "app.py")
if ($Headless) { $streamlitArgs += @("--server.headless", "true") }
& python -m streamlit @streamlitArgs
