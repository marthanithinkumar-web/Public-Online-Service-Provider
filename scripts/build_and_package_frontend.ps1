param(
    [switch]$CopyToBackend
)

# Determine project root (one level up from scripts folder)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Resolve-Path (Join-Path $scriptDir '..')
$frontendDir = Join-Path $projectRoot 'frontend'
$backendStatic = Join-Path $projectRoot 'backend\static'

Write-Output "Project root: $projectRoot"
Write-Output "Frontend dir: $frontendDir"

if (-not (Test-Path (Join-Path $frontendDir 'package.json'))) {
    Write-Error "package.json not found in $frontendDir. Are you in the correct project?"
    exit 1
}

# Check for npm
$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Error "npm not found on PATH. Please install Node.js (LTS) from https://nodejs.org/ then re-run this script. Opening the download page now..."
    Start-Process 'https://nodejs.org/en/download/'
    exit 2
}

# Run install and build
Push-Location $frontendDir
try {
    if (Test-Path 'package-lock.json') {
        Write-Output "Running npm ci..."
        npm ci
    } else {
        Write-Output "Running npm install..."
        npm install
    }

    Write-Output "Running npm run build..."
    npm run build
} catch {
    Write-Error "Frontend build failed: $_"
    Pop-Location
    exit 3
}

Pop-Location

$distDir = Join-Path $frontendDir 'dist'
if (-not (Test-Path $distDir)) {
    Write-Error "Build completed but dist/ not found at $distDir"
    exit 4
}

# Create ZIP in frontend folder and at project root
$destZipFrontend = Join-Path $frontendDir 'dist.zip'
$destZipRoot = Join-Path $projectRoot 'frontend_dist.zip'

Write-Output "Creating ZIP: $destZipFrontend"
Compress-Archive -Path "$distDir\*" -DestinationPath $destZipFrontend -Force
Write-Output "Also creating ZIP: $destZipRoot"
Compress-Archive -Path "$distDir\*" -DestinationPath $destZipRoot -Force

if ($CopyToBackend) {
    if (-not (Test-Path $backendStatic)) {
        New-Item -ItemType Directory -Path $backendStatic -Force | Out-Null
    }
    Write-Output "Copying dist -> backend/static..."
    Copy-Item -Path "$distDir\*" -Destination $backendStatic -Recurse -Force
    if (Test-Path (Join-Path $backendStatic 'index.html')) {
        Write-Output "Copy successful. index.html found in backend/static"
    } else {
        Write-Error "Copy completed but index.html missing in backend/static"
    }
}

Write-Output "Frontend build and packaging finished. Upload or leave dist.zip at: $destZipFrontend"
Write-Output "Also: $destZipRoot"
Write-Output "If you want me to continue creating the final extra_final.zip, upload dist.zip into the project frontend folder or run this script with -CopyToBackend and then reply 'done'."