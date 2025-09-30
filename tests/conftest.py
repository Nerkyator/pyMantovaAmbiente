"""Test fixtures for Mantova Ambiente integration."""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.mantova_ambiente.const import (
    CONF_CACHE_HOURS,
    CONF_WASTE_CODES,
    CONF_ZONE,
    DOMAIN,
)
from custom_components.mantova_ambiente.models import MantovaAmbienteData, RecyclingCollection


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return ConfigEntry(
        version=1,
        minor_version=0,
        domain=DOMAIN,
        title="Mantova Ambiente Zone 3631",
        data={
            CONF_ZONE: "3631",
            CONF_CACHE_HOURS: 24,
            CONF_WASTE_CODES: ["3707", "3708", "3710"],
        },
        source="user",
        entry_id="test_entry_id",
    )


@pytest.fixture
def mock_api_response():
    """Return mock API response data."""
    return {
        "data": [
            {
                "id": "3707",
                "title": "Organic Waste",
                "collections": [
                    "2025-10-01 06:00:00",
                    "2025-10-03 06:00:00",
                    "2025-10-05 06:00:00",
                ]
            },
            {
                "id": "3708", 
                "title": "Paper and Cardboard",
                "collections": [
                    "2025-10-02 06:00:00",
                    "2025-10-09 06:00:00",
                    "2025-10-16 06:00:00",
                ]
            },
            {
                "id": "3710",
                "title": "Plastic and Metal",
                "collections": [
                    "2025-10-04 06:00:00",
                    "2025-10-11 06:00:00",
                    "2025-10-18 06:00:00",
                ]
            }
        ]
    }


@pytest.fixture
def mock_recycling_collections():
    """Return mock RecyclingCollection objects."""
    return [
        RecyclingCollection(
            id="3707",
            title="Organic Waste",
            collections=[
                datetime(2025, 10, 1, 6, 0, 0),
                datetime(2025, 10, 3, 6, 0, 0),
                datetime(2025, 10, 5, 6, 0, 0),
            ]
        ),
        RecyclingCollection(
            id="3708",
            title="Paper and Cardboard", 
            collections=[
                datetime(2025, 10, 2, 6, 0, 0),
                datetime(2025, 10, 9, 6, 0, 0),
                datetime(2025, 10, 16, 6, 0, 0),
            ]
        ),
        RecyclingCollection(
            id="3710",
            title="Plastic and Metal",
            collections=[
                datetime(2025, 10, 4, 6, 0, 0),
                datetime(2025, 10, 11, 6, 0, 0),
                datetime(2025, 10, 18, 6, 0, 0),
            ]
        )
    ]


@pytest.fixture
def mock_mantova_ambiente_data(mock_recycling_collections):
    """Return mock MantovaAmbienteData."""
    return MantovaAmbienteData(
        collections=mock_recycling_collections,
        last_update=datetime(2025, 9, 30, 12, 0, 0)
    )


@pytest.fixture
def mock_cache_file_content(mock_mantova_ambiente_data):
    """Return mock cache file content."""
    return {
        "last_update": mock_mantova_ambiente_data.last_update.isoformat(),
        "collections": [
            {
                "id": collection.id,
                "title": collection.title,
                "collections": [dt.isoformat() for dt in collection.collections]
            }
            for collection in mock_mantova_ambiente_data.collections
        ]
    }