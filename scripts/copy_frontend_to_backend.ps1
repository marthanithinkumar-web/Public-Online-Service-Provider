# PowerShell script to copy frontend/dist to backend/static
param(
    [string]$FrontendDist = "..\frontend\dist",
    [string]$BackendStatic = "..\backend\static"
)

if (-not (Test-Path $FrontendDist)) {
    Write-Error "Frontend dist not found at $FrontendDist. Run frontend build first."
    exit 1
}

if (-not (Test-Path $BackendStatic)) {
    New-Item -ItemType Directory -Path $BackendStatic -Force | Out-Null
}

Write-Output "Copying $FrontendDist -> $BackendStatic"
Copy-Item -Path "$FrontendDist\*" -Destination $BackendStatic -Recurse -Force
Write-Output "Done."
