import os
from dotenv import load_dotenv

# Force reload .env file to override any existing environment variables
load_dotenv(override=True)


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Change this line to switch between models - "openai" or "gemini"
    AI_MODEL_PROVIDER: str = "openai"  # <-- Change this to switch models

    # Model names with fallbacks for empty environment variables
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL") or "models/gemini-1.5-flash-latest"
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "your-secret-key")


settings = Settings()