"""Data models for Mantova Ambiente integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List


@dataclass
class RecyclingCollection:
    """Represents a recycling collection schedule."""
    
    id: str
    title: str
    collections: List[datetime]
    
    def __post_init__(self):
        """Ensure collections are sorted by date."""
        self.collections.sort()
    
    @property
    def next_collection(self) -> datetime | None:
        """Get the next collection date."""
        now = datetime.now()
        for collection_date in self.collections:
            if collection_date > now:
                return collection_date
        return None
    
    @property
    def next_collections(self) -> List[datetime]:
        """Get all future collection dates."""
        now = datetime.now()
        return [date for date in self.collections if date > now]
    
    def is_collection_tomorrow(self) -> bool:
        """Check if there's a collection tomorrow."""
        tomorrow = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = tomorrow + timedelta(days=1)
        tomorrow_end = tomorrow.replace(hour=23, minute=59, second=59)
        
        return any(
            tomorrow <= collection_date <= tomorrow_end
            for collection_date in self.collections
        )


@dataclass
class MantovaAmbienteData:
    """Container for all Mantova Ambiente data."""
    
    collections: List[RecyclingCollection]
    last_update: datetime
    
    def get_collection_by_id(self, collection_id: str) -> RecyclingCollection | None:
        """Get a collection by its ID."""
        for collection in self.collections:
            if collection.id == collection_id:
                return collection
        return None
    
    def get_tomorrow_collections(self) -> List[RecyclingCollection]:
        """Get all collections scheduled for tomorrow."""
        return [
            collection for collection in self.collections
            if collection.is_collection_tomorrow()
        ]