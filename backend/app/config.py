import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    AI_MODEL_PROVIDER: str = os.getenv("AI_MODEL_PROVIDER", "openai")  # gemini or openai
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-8b")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "your-secret-key")


settings = Settings()