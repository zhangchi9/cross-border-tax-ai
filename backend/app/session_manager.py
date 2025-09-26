from typing import Dict, Optional
import uuid
from datetime import datetime

from .models import CaseFile, ChatMessage, MessageRole


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, CaseFile] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        case_file = CaseFile(session_id=session_id)

        # Add welcome message
        welcome_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content="This is general information, not legal or tax advice. Consult a qualified professional."
        )
        case_file.messages.append(welcome_message)

        self._sessions[session_id] = case_file
        return session_id

    def get_session(self, session_id: str) -> Optional[CaseFile]:
        return self._sessions.get(session_id)

    def update_session(self, session_id: str, case_file: CaseFile) -> None:
        if session_id in self._sessions:
            case_file.updated_at = datetime.now()
            self._sessions[session_id] = case_file

    def add_message(self, session_id: str, role: MessageRole, content: str) -> Optional[CaseFile]:
        case_file = self.get_session(session_id)
        if case_file:
            message = ChatMessage(role=role, content=content)
            case_file.messages.append(message)
            case_file.updated_at = datetime.now()
            self._sessions[session_id] = case_file
            return case_file
        return None

    def list_sessions(self) -> Dict[str, CaseFile]:
        return self._sessions.copy()

    def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


# Global session manager instance
session_manager = SessionManager()