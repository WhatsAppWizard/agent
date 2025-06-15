from datetime import datetime
from typing import Optional, Dict, Any

class User:
    def __init__(self, user_id: str, created_at: Optional[datetime] = None, last_active: Optional[datetime] = None, preferences: Optional[Dict[str, Any]] = None):
        self.id = user_id
        self.created_at = created_at or datetime.utcnow()
        self.last_active = last_active or datetime.utcnow()
        self.preferences = preferences or {} 