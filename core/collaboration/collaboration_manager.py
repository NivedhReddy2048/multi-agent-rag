"""Shared Workspaces & Multi-User Collaboration Engine."""

import time
import uuid
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from core.logger import get_logger

logger = get_logger("core.collaboration.manager")


class SharedWorkspaceItem(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    item_type: str  # 'notebook', 'collection', 'bookmark'
    content: Dict[str, Any]
    owner_id: str
    collaborators: Set[str] = Field(default_factory=set)
    updated_at: float = Field(default_factory=time.time)


class CollaborationManager:
    """Manages shared multi-user notebooks, collections, and team research workspaces."""

    def __init__(self):
        self._items: Dict[str, SharedWorkspaceItem] = {}

    def create_shared_item(self, title: str, item_type: str, content: Dict[str, Any], owner_id: str) -> SharedWorkspaceItem:
        item = SharedWorkspaceItem(title=title, item_type=item_type, content=content, owner_id=owner_id)
        item.collaborators.add(owner_id)
        self._items[item.item_id] = item
        logger.info(f"Created shared workspace item '{title}' (ID: {item.item_id}) by '{owner_id}'")
        return item

    def share_with_user(self, item_id: str, user_id: str, owner_id: str):
        if item_id in self._items:
            item = self._items[item_id]
            if item.owner_id != owner_id:
                raise PermissionError("Only the item owner can grant access.")
            item.collaborators.add(user_id)
            logger.info(f"Granted user '{user_id}' collaboration access to '{item_id}'")

    def update_item(self, item_id: str, new_content: Dict[str, Any], user_id: str):
        if item_id in self._items:
            item = self._items[item_id]
            if user_id not in item.collaborators:
                raise PermissionError("User is not a collaborator on this item.")
            item.content = new_content
            item.updated_at = time.time()

    def list_accessible_items(self, user_id: str) -> List[SharedWorkspaceItem]:
        return [i for i in self._items.values() if user_id in i.collaborators]


# Global singleton instance
collaboration_manager = CollaborationManager()
