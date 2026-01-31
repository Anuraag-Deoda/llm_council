"""
Simple JSON-based storage for conversation history.
"""
import json
import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
from ..models import ConversationHistory, ChatMessage, CouncilResponse


class ConversationStorage:
    """Manages conversation persistence using JSON files."""

    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database file if it doesn't exist
        if not self.database_path.exists():
            self._save_data({})

    def _load_data(self) -> Dict:
        """Load all conversations from disk."""
        try:
            with open(self.database_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_data(self, data: Dict):
        """Save all conversations to disk."""
        with open(self.database_path, "w") as f:
            json.dump(data, f, indent=2)

    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        data = self._load_data()

        now = datetime.now().timestamp()
        conversation = ConversationHistory(
            conversation_id=conversation_id,
            messages=[],
            council_responses=[],
            created_at=now,
            updated_at=now,
        )

        data[conversation_id] = conversation.model_dump()
        self._save_data(data)

        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[ConversationHistory]:
        """Retrieve a conversation by ID."""
        data = self._load_data()
        conv_data = data.get(conversation_id)

        if conv_data:
            return ConversationHistory(**conv_data)
        return None

    def add_message(
        self, conversation_id: str, role: str, content: str
    ) -> ConversationHistory:
        """Add a message to a conversation."""
        data = self._load_data()

        if conversation_id not in data:
            raise ValueError(f"Conversation {conversation_id} not found")

        message = ChatMessage(
            role=role, content=content, timestamp=datetime.now().timestamp()
        )

        data[conversation_id]["messages"].append(message.model_dump())
        data[conversation_id]["updated_at"] = datetime.now().timestamp()

        self._save_data(data)
        return ConversationHistory(**data[conversation_id])

    def add_council_response(
        self, conversation_id: str, council_response: CouncilResponse
    ) -> ConversationHistory:
        """Add a council response to a conversation."""
        data = self._load_data()

        if conversation_id not in data:
            raise ValueError(f"Conversation {conversation_id} not found")

        data[conversation_id]["council_responses"].append(
            council_response.model_dump()
        )
        data[conversation_id]["updated_at"] = datetime.now().timestamp()

        self._save_data(data)
        return ConversationHistory(**data[conversation_id])

    def list_conversations(self) -> List[ConversationHistory]:
        """List all conversations."""
        data = self._load_data()
        return [ConversationHistory(**conv) for conv in data.values()]

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        data = self._load_data()

        if conversation_id in data:
            del data[conversation_id]
            self._save_data(data)
            return True

        return False
