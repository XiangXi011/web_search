# Search Gateway Deployment Script for Windows + Docker Desktop
# Run this in PowerShell as Administrator

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Search Gateway Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker not found. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

try {
    $composeVersion = docker compose version
    Write-Host "Docker Compose found: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Docker Compose not found." -ForegroundColor Red
    exit 1
}

# Navigate to project directory
Set-Location $ProjectDir
Write-Host "Project directory: $ProjectDir" -ForegroundColor Gray

# Pull and build
Write-Host "`n[1/4] Building and starting services..." -ForegroundColor Yellow
docker compose up --build -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: docker compose up failed." -ForegroundColor Red
    exit 1
}

# Wait for services to be ready
Write-Host "`n[2/4] Waiting for services to start (15s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Check container status
Write-Host "`n[3/4] Checking container status..." -ForegroundColor Yellow
$containers = docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
Write-Host $containers

# Health check
Write-Host "`n[4/4] Health check..." -ForegroundColor Yellow

try {
    $health = Invoke-RestMethod -Uri "http://localhost:8011/health" -TimeoutSec 5
    Write-Host "Gateway Health: $($health | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "Gateway health check failed (may still be starting): $_" -ForegroundColor Yellow
}

try {
    $ready = Invoke-RestMethod -Uri "http://localhost:8011/ready" -TimeoutSec 5
    Write-Host "Gateway Ready: $($ready | ConvertTo-Json)" -ForegroundColor Green
} catch {
    Write-Host "Gateway ready check failed (may still be starting): $_" -ForegroundColor Yellow
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Deployment Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Search Gateway: http://localhost:8011" -ForegroundColor White
Write-Host "SearXNG:        http://localhost:8080" -ForegroundColor White
Write-Host "Redis:          localhost:6379" -ForegroundColor White
Write-Host "`nTest search:" -ForegroundColor Gray
Write-Host '  curl -X POST http://localhost:8011/v1/search -H "Content-Type: application/json" -d \'{\"query\":\"FastAPI tutorial\",\"profile\":\"auto\"}\'' -ForegroundColor Gray
Write-Host "`nTo stop:  docker compose down" -ForegroundColor Gray
Write-Host "To logs:  docker compose logs -f" -ForegroundColor Gray
