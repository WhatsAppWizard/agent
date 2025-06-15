from datetime import datetime
from typing import Optional

class Message:
    def __init__(self, role: str, content: str, timestamp: Optional[datetime] = None):
        self.role = role
        self.content = content
        self.timestamp = timestamp or datetime.utcnow() 