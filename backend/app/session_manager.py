from typing import Dict, Optional
import uuid
from datetime import datetime

from .models import CaseFile, ChatMessage, MessageRole, ConversationPhase


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, CaseFile] = {}

    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        case_file = CaseFile(session_id=session_id)

        # Add welcome message
        welcome_message = ChatMessage(
            role=MessageRole.ASSISTANT,
            content="Hi, I am your cross-border tax consultant. Please explain your tax situation in a few words."
        )
        case_file.messages.append(welcome_message)

        self._sessions[session_id] = case_file
        return session_id

    def get_session(self, session_id: str) -> Optional[CaseFile]:
        case_file = self._sessions.get(session_id)
        if case_file:
            # Migrate messages to add IDs if missing
            self._migrate_message_ids(case_file)
        return case_file

    def _migrate_message_ids(self, case_file: CaseFile) -> None:
        """Add IDs to messages that don't have them"""
        for message in case_file.messages:
            if not hasattr(message, 'id') or not message.id:
                message.id = str(uuid.uuid4())

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

    def edit_message_and_truncate(self, session_id: str, message_id: str, new_content: str) -> Optional[CaseFile]:
        """Edit a user message and remove all messages after it"""
        case_file = self.get_session(session_id)
        if not case_file:
            return None

        # Find the message to edit
        message_index = None
        for i, msg in enumerate(case_file.messages):
            if msg.id == message_id and msg.role == MessageRole.USER:
                message_index = i
                break

        if message_index is None:
            return None  # Message not found or not a user message

        # Update the message content
        case_file.messages[message_index].content = new_content
        case_file.messages[message_index].timestamp = datetime.now()

        # Remove all messages after the edited message
        case_file.messages = case_file.messages[:message_index + 1]

        # Reset conversation phase and user profile if needed
        # We'll need to reprocess the conversation from the beginning
        self._reset_case_file_state(case_file)

        case_file.updated_at = datetime.now()
        self._sessions[session_id] = case_file

        return case_file

    def _reset_case_file_state(self, case_file: CaseFile) -> None:
        """Reset case file state when conversation is edited"""
        # Keep the basic profile but reset derived state
        case_file.conversation_phase = ConversationPhase.INTAKE
        case_file.potential_issues = []
        case_file.unanswered_questions = []
        # Keep user_profile, jurisdictions, and income_types as they may still be valid


# Global session manager instance
session_manager = SessionManager()