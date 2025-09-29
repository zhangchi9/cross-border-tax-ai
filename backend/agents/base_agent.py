"""
Base agent class for the cross-border tax system
"""
import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional

class TaxAgent(ABC):
    """Abstract base class for tax agents"""

    def __init__(self, name: str, knowledge_base_path: Optional[str] = None):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
        self.knowledge_base = {}

        if knowledge_base_path:
            self.knowledge_base = self.load_knowledge_base(knowledge_base_path)

    def load_knowledge_base(self, path: str) -> Dict[str, Any]:
        """Load knowledge base from JSON file"""
        try:
            kb_path = Path(__file__).parent.parent / "data" / "knowledge_base" / path
            with open(kb_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Knowledge base file not found: {path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in knowledge base {path}: {e}")
            return {}

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output"""
        pass

    def log_interaction(self, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        """Log agent interaction for audit trail"""
        self.logger.info(f"Agent {self.name} processed input: {input_data}")
        self.logger.info(f"Agent {self.name} generated output: {output_data}")


class AgentSession:
    """Manages session state between agents"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.context = {}
        self.history = []
        self.created_at = None
        self.updated_at = None

    def update_context(self, key: str, value: Any):
        """Update session context"""
        self.context[key] = value
        self.updated_at = self._current_timestamp()

    def add_to_history(self, agent_name: str, input_data: Dict, output_data: Dict):
        """Add interaction to session history"""
        self.history.append({
            "agent": agent_name,
            "timestamp": self._current_timestamp(),
            "input": input_data,
            "output": output_data
        })

    def _current_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


class AgentOrchestrator:
    """Orchestrates communication between agents"""

    def __init__(self):
        self.agents = {}
        self.sessions = {}

    def register_agent(self, agent: TaxAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent.name] = agent

    def create_session(self, session_id: str) -> AgentSession:
        """Create a new session"""
        session = AgentSession(session_id)
        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get existing session"""
        return self.sessions.get(session_id)

    def route_to_agent(self, agent_name: str, session_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route input to specific agent and manage session"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")

        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)

        agent = self.agents[agent_name]

        # Add session context to input
        enhanced_input = {
            **input_data,
            "session_context": session.context
        }

        # Process with agent
        output = agent.process(enhanced_input)

        # Update session
        session.add_to_history(agent_name, input_data, output)

        # Log interaction
        agent.log_interaction(enhanced_input, output)

        return output