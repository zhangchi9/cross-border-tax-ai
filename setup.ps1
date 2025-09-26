# Cross-Border Tax Consultant - Initial Setup Script
Write-Host "Cross-Border Tax Consultant - Initial Setup" -ForegroundColor Green
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env file. Please update with your API keys." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host ".env file already exists." -ForegroundColor Blue
    Write-Host ""
}

# Build Docker images
Write-Host "Building Docker images..." -ForegroundColor Cyan
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Setup complete! Next steps:" -ForegroundColor Green
    Write-Host "1. Edit .env file and add your GEMINI_API_KEY" -ForegroundColor Yellow
    Write-Host "2. Run: docker-compose up -d" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Cyan
    Write-Host "  docker-compose up -d                    # Start production mode"
    Write-Host "  docker-compose -f docker-compose.dev.yml up  # Start dev mode"
    Write-Host "  docker-compose down                     # Stop application"
    Write-Host "  docker-compose logs -f                  # View logs"
} else {
    Write-Host "Error occurred during setup. Please check Docker installation." -ForegroundColor Red
}