"""
Cross-Border Tax Agents Package

This package contains the LLM-powered agentic framework for cross-border tax consultation.

LLM Intake Agent: Conducts intelligent client consultation and assigns tags using LLM
LLM Forms Analysis Agent: Analyzes tags to determine required forms using LLM

Usage:
    from agents import LLMCrossBorderTaxOrchestrator

    # Initialize LLM orchestrator
    orchestrator = LLMCrossBorderTaxOrchestrator()

    # Start consultation
    response = await orchestrator.start_consultation("I'm a U.S. citizen living in Canada")

    # Continue consultation
    response = await orchestrator.continue_consultation(session_id, "Yes, I have rental property")
"""

from .base_agent import TaxAgent, AgentSession, AgentOrchestrator
from .llm_intake_agent import LLMIntakeAgent
from .llm_forms_analysis_agent import LLMFormsAnalysisAgent
from .llm_orchestrator import LLMCrossBorderTaxOrchestrator

__all__ = [
    'TaxAgent',
    'AgentSession',
    'AgentOrchestrator',
    'LLMIntakeAgent',
    'LLMFormsAnalysisAgent',
    'LLMCrossBorderTaxOrchestrator'
]