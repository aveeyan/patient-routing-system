# schemas/chat.py

"""Schema for chat"""

# Standard Imports
from dataclasses import dataclass

# Third Party Imports
# Local Imports

@dataclass
class ChatSession:
    session_id: str
    created_at: str

@dataclass
class ConversationMessage:
    role: str
    content: str
    timestamp: str
