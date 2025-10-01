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

    # Phase 2: LLM Intelligence Features (Feature Flags)
    USE_LLM_TAG_ASSIGNMENT: bool = True  # Enable LLM-based tag analysis with confidence scoring
    USE_LLM_QUESTION_SELECTION: bool = False  # Enable LLM-driven question selection (set to True to activate)

    # When False, falls back to deterministic keyword matching and sequential question flow

    # Phase 3: Enhanced Features (Feature Flags)
    USE_MULTI_FACT_EXTRACTION: bool = True  # Extract all facts from each response
    USE_SMART_MODULE_SKIPPING: bool = True  # Skip irrelevant modules based on context
    USE_EXPLANATION_GENERATION: bool = True  # Explain why asking each question
    USE_AUTO_CLARIFICATION: bool = True  # Automatically ask clarifications for low confidence
    USE_ADAPTIVE_FOLLOWUPS: bool = True  # Ask intelligent follow-up questions
    USE_VERIFICATION_PHASE: bool = True  # Verify low/medium confidence tags before forms analysis
    USE_PROGRESSIVE_ASSIGNMENT: bool = True  # Assign tags from any response, not just direct questions
    USE_CONTEXT_CORRECTION: bool = True  # Allow users to correct previous answers

    # Phase 3 features dramatically improve UX but increase LLM costs


science_config = ScienceConfig()