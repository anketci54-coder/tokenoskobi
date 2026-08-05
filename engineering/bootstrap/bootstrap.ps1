$ErrorActionPreference = "Stop"

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

if(Test-Path "tools\tokenoskobi_healthcheck.py"){
    python tools\tokenoskobi_healthcheck.py
}
else{
    Write-Host "Health check missing."
}

Write-Host ""
Write-Host "[6/7] Checking Engineering..."

Get-ChildItem engineering

Write-Host ""
Write-Host "[7/7] Bootstrap Completed"

Write-Host ""
Write-Host "Repository is ready for development."
Write-Host ""
