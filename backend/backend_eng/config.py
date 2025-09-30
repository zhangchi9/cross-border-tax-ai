"""
Backend Engineering Configuration

API configuration, CORS settings, and backend-specific configurations.
"""
import os
from dotenv import load_dotenv

# Force reload .env file to override any existing environment variables
load_dotenv(override=True)


class BackendConfig:
    """Configuration for backend engineering"""

    # CORS Configuration
    CORS_ORIGINS: list = [
        "http://localhost:5173",  # Frontend dev
        "http://localhost:3000",  # Frontend production
    ]

    # Session Configuration
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "your-secret-key")

    # API Configuration
    API_TITLE: str = "Cross-Border Tax Consultant API"
    API_VERSION: str = "1.0.0"

    # Streaming Configuration
    STREAMING_CHAR_DELAY: float = 0.01  # Delay per character in streaming
    STREAMING_FORCE_FINAL_DELAY: float = 0.005  # Faster delay for force final


backend_config = BackendConfig()