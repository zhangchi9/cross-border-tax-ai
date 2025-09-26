@echo off
echo Cross-Border Tax Consultant - Initial Setup
echo.

if not exist .env (
    copy .env.example .env
    echo Created .env file. Please update with your API keys.
    echo.
) else (
    echo .env file already exists.
    echo.
)

echo Building Docker images...
docker-compose build

echo.
echo Setup complete! Next steps:
echo 1. Edit .env file and add your GEMINI_API_KEY
echo 2. Run: make up (or docker-compose up -d)
echo.
pause