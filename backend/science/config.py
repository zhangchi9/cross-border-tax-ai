"""
Science Module Configuration

AI model selection and configuration for the science team.
"""
import os
from dotenv import load_dotenv

# Force reload .env file to override any existing environment variables
load_dotenv(override=True)


class ScienceConfig:
    """Configuration for AI models and science module"""

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Change this line to switch between models - "openai" or "gemini"
    AI_MODEL_PROVIDER: str = "openai"  # <-- Change this to switch models

    # Model names with fallbacks for empty environment variables
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL") or "models/gemini-1.5-flash-latest"
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL") or "gpt-4o-mini"

    # LLM Configuration
    LLM_TEMPERATURE: float = 0.1

    # Workflow Configuration
    WORKFLOW_RECURSION_LIMIT: int = 25
    MIN_TAGS_FOR_TRANSITION: int = 2
    MIN_CONVERSATION_LENGTH: int = 6


science_config = ScienceConfig()