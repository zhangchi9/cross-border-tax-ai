import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "your-secret-key")


settings = Settings()