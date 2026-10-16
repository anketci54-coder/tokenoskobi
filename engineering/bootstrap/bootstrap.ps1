$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..\..")

Write-Host ""
Write-Host "==============================================="
Write-Host " TOKENOSKOBI ENGINEERING BOOTSTRAP"
Write-Host "==============================================="
Write-Host ""

Write-Host "[1/7] Checking Python..."

try {
    python --version
}
catch {
    Write-Host "Python not found."
    exit 1
}

Write-Host ""
Write-Host "[2/7] Checking Git..."

try {
    git rev-parse --is-inside-work-tree | Out-Null
    Write-Host "Git repository detected."
}
catch {
    Write-Host "Not inside Git repository."
    exit 1
}

Write-Host ""
Write-Host "[3/7] Creating engineering folders..."

$folders = @(
    "engineering\reports",
    "engineering\logs",
    "engineering\cache",
    "engineering\temp"
)

foreach($folder in $folders){
    New-Item -ItemType Directory -Force $folder | Out-Null
}

Write-Host "Done."

Write-Host ""
Write-Host "[4/7] Checking requirements..."

if(Test-Path "requirements.txt"){
    Write-Host "requirements.txt found."
}
else{
    Write-Host "requirements.txt NOT FOUND."
}

Write-Host ""
Write-Host "[5/7] Checking Health Check..."
Write-Host ""
Write-Host "[Repository Validator]"

python engineering\health\repository_validator.py

if(Test-Path "scripts\engineering\tokenoskobi_healthcheck.py"){
    python scripts\engineering\tokenoskobi_healthcheck.py
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
else{
    Write-Host "Health check missing."
    exit 1
}

Write-Host ""
Write-Host "[6/7] Checking Engineering..."

Get-ChildItem engineering

Write-Host ""
Write-Host "[7/7] Bootstrap Completed"

Write-Host ""
Write-Host "Repository is ready for development."
Write-Host ""
