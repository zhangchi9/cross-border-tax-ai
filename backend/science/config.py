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
    # Can be overridden with AI_MODEL_PROVIDER environment variable
    AI_MODEL_PROVIDER: str = os.getenv("AI_MODEL_PROVIDER", "openai")  # <-- Change this to switch models

    # Model names with fallbacks for empty environment variables
    # Note: Gemini models use format "gemini-1.5-pro" or "gemini-1.5-flash" (langchain adds "models/" prefix)
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL") or "gemini-1.5-pro"
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL") or "gpt-5"

    # LLM Configuration
    LLM_TEMPERATURE: float = 0.1

    # Workflow Configuration
    WORKFLOW_RECURSION_LIMIT: int = 25
    MIN_TAGS_FOR_TRANSITION: int = 6  # Increased from 2 to prevent premature transition
    MIN_CONVERSATION_LENGTH: int = 24  # Increased from 6 to ensure thorough intake (12 Q&A pairs)
    MIN_GATING_QUESTIONS_ASKED: int = 8  # Minimum gating questions before allowing transition
    MIN_QUESTIONS_BEFORE_SKIPPING: int = 5  # Ask at least 5 questions before LLM can skip questions

    # Phase 2: LLM Intelligence Features (Feature Flags)
    USE_LLM_TAG_ASSIGNMENT: bool = True  # Enable LLM-based tag analysis with confidence scoring
    USE_LLM_QUESTION_SELECTION: bool = False  # Enable LLM-driven question selection (set to True to activate)
    USE_LLM_QUESTION_SKIPPING: bool = True  # Enable LLM-based intelligent question skipping (replaces rule-based)

    # When False, falls back to deterministic keyword matching and sequential question flow

    # Phase 3: Enhanced Features (Feature Flags)
    USE_MULTI_FACT_EXTRACTION: bool = True  # Extract all facts from each response
    USE_SMART_MODULE_SKIPPING: bool = True  # Skip irrelevant modules based on context
    USE_EXPLANATION_GENERATION: bool = True  # Explain why asking each question
    USE_AUTO_CLARIFICATION: bool = False  # DISABLED - causes repeated question loops
    USE_ADAPTIVE_FOLLOWUPS: bool = False  # DISABLED - causes repeated question loops
    USE_VERIFICATION_PHASE: bool = False  # DISABLED - causes repeated question loops
    USE_PROGRESSIVE_ASSIGNMENT: bool = True  # Assign tags from any response, not just direct questions
    USE_CONTEXT_CORRECTION: bool = True  # Allow users to correct previous answers

    # Phase 3 features dramatically improve UX but increase LLM costs
    # NOTE: Clarification, follow-ups, and verification temporarily disabled due to repeated question bugs


science_config = ScienceConfig()