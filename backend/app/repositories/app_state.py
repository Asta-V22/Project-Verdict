"""
AppState repository — data access for application state.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.app_state import AppState
from app.repositories.base import BaseRepository


class AppStateRepository(BaseRepository[AppState]):
    """Repository for key-value application state."""

    def __init__(self, session: Session) -> None:
        super().__init__(AppState, session)

    def get_value(self, key: str) -> Any | None:
        """Get and deserialize a JSON value by key."""
        record = self.get_by_id(key)
        if record:
            try:
                return json.loads(record.value)
            except json.JSONDecodeError:
                return record.value
        return None

    def set_value(self, key: str, value: Any) -> AppState:
        """Serialize and set a JSON value by key. Caller must commit."""
        record = self.get_by_id(key)
        json_value = json.dumps(value)
        if record:
            record.value = json_value
        else:
            record = AppState(key=key, value=json_value)
            self.session.add(record)
        self.session.flush()
        return record
