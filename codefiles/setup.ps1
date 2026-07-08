#Requires -Version 5.1
<#
.SYNOPSIS
    One-shot bootstrap: download the repo zip, extract it, and launch the app.

.DESCRIPTION
    Downloads the GitHub repository archive, extracts it, locates the folder that
    contains app.py, and then calls run.ps1 (install deps -> .env -> az login -> run).

    Edit the default -ZipUrl below to point at YOUR GitHub repo's archive link, e.g.
        https://github.com/<your-org>/<your-repo>/archive/refs/heads/main.zip

.EXAMPLE
    ./setup.ps1
        Uses the default ZipUrl and installs under %USERPROFILE%\DataSecurityAgent.

.EXAMPLE
    ./setup.ps1 -ZipUrl "https://github.com/me/myrepo/archive/refs/heads/main.zip" -InstallDir "C:\Code"
#>
[CmdletBinding()]
param(
    # >>> Replace with your repository's archive URL before sharing <<<
    [string]$ZipUrl = "https://github.com/<your-org>/<your-repo>/archive/refs/heads/main.zip",
    [string]$InstallDir = (Join-Path $env:USERPROFILE "DataSecurityAgent")
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

Write-Host "=== Data Security & Compliance Agent : bootstrap ===" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
$zipPath = Join-Path $InstallDir "app.zip"

Write-Host "Downloading $ZipUrl ..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $ZipUrl -OutFile $zipPath

Write-Host "Extracting to $InstallDir ..." -ForegroundColor Yellow
Expand-Archive -Path $zipPath -DestinationPath $InstallDir -Force
Remove-Item $zipPath -Force

# Locate the folder that has BOTH app.py and requirements.txt (handles any nesting)
$appFile = Get-ChildItem -Path $InstallDir -Recurse -Filter "app.py" -ErrorAction SilentlyContinue |
    Where-Object { Test-Path (Join-Path $_.DirectoryName "requirements.txt") } |
    Select-Object -First 1

if (-not $appFile) {
    Write-Host "Could not find app.py (with requirements.txt) after extraction." -ForegroundColor Red
    exit 1
}

$codeDir = $appFile.DirectoryName
Write-Host "App folder: $codeDir" -ForegroundColor Green

Set-Location $codeDir
& (Join-Path $codeDir "run.ps1")
