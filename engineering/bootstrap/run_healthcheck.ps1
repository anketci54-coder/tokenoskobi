Write-Host ""
Write-Host "============================================="
Write-Host " TOKENOSKOBI ENGINEERING HEALTHCHECK"
Write-Host "============================================="
Write-Host ""

python (Join-Path $PSScriptRoot "..\..\scripts\engineering\tokenoskobi_healthcheck.py")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Health Check Finished."
