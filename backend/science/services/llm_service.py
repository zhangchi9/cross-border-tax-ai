"""
LLM Service

Centralized LLM initialization and configuration.
"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from science.config import science_config


def get_llm():
    """
    Initialize and return the configured LLM based on provider settings.

    Returns:
        Configured LLM instance (ChatOpenAI or ChatGoogleGenerativeAI)

    Raises:
        ValueError: If an unsupported AI model provider is configured
    """
    if science_config.AI_MODEL_PROVIDER == "openai":
        return ChatOpenAI(
            model=science_config.OPENAI_MODEL,
            temperature=science_config.LLM_TEMPERATURE,
            api_key=science_config.OPENAI_API_KEY
        )
    elif science_config.AI_MODEL_PROVIDER == "gemini":
        return ChatGoogleGenerativeAI(
            model=science_config.GEMINI_MODEL,
            temperature=science_config.LLM_TEMPERATURE,
            google_api_key=science_config.GEMINI_API_KEY
        )
    else:
        raise ValueError(
            f"Unsupported AI model provider: {science_config.AI_MODEL_PROVIDER}. "
            "Supported providers: 'openai', 'gemini'"
        )