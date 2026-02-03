"""
Backward-compatible storage wrapper for existing routes
"""
import json
import uuid
from typing import Optional, List, Dict, Any, Union
from pathlib import Path


class ConversationStorage:
    """
    Legacy JSON-based conversation storage
    Kept for backward compatibility with existing routes
    """

    def __init__(self, database_path: str):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.database_path.exists():
            self._save_data({"conversations": {}})

    def _load_data(self) -> Dict[str, Any]:
        """Load data from JSON file"""
        try:
            with open(self.database_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"conversations": {}}

    def _save_data(self, data: Dict[str, Any]) -> None:
        """Save data to JSON file"""
        with open(self.database_path, 'w') as f:
            json.dump(data, f, indent=2)

    def create_conversation(self, conversation_id: Optional[str] = None, initial_data: Optional[Dict] = None) -> str:
        """Create a new conversation"""
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        data = self._load_data()
        conversation = {
            "id": conversation_id,
            "messages": [],
            **(initial_data or {})
        }
        data["conversations"][conversation_id] = conversation
        self._save_data(data)
        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a conversation by ID"""
        data = self._load_data()
        return data["conversations"].get(conversation_id)

    def add_message(self, conversation_id: str, role: str, content: str) -> None:
        """Add a message to a conversation"""
        data = self._load_data()
        if conversation_id in data["conversations"]:
            message = {"role": role, "content": content}
            data["conversations"][conversation_id]["messages"].append(message)
            self._save_data(data)

    def add_council_response(self, conversation_id: str, response: Any) -> None:
        """Add a council response to a conversation"""
        data = self._load_data()
        if conversation_id in data["conversations"]:
            if "council_responses" not in data["conversations"][conversation_id]:
                data["conversations"][conversation_id]["council_responses"] = []
            # Convert Pydantic model to dict if needed
            response_data = response.model_dump() if hasattr(response, 'model_dump') else response
            data["conversations"][conversation_id]["council_responses"].append(response_data)
            self._save_data(data)

    def list_conversations(self) -> List[Dict]:
        """List all conversations (alias for get_all_conversations)"""
        return self.get_all_conversations()

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation by ID"""
        data = self._load_data()
        if conversation_id in data["conversations"]:
            del data["conversations"][conversation_id]
            self._save_data(data)
            return True
        return False

    def get_all_conversations(self) -> List[Dict]:
        """Get all conversations"""
        data = self._load_data()
        return list(data["conversations"].values())
