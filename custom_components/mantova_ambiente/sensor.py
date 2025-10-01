"""Sensor platform for Mantova Ambiente integration."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_NEXT_DATES,
    ATTR_WASTE_TYPE,
    ATTR_ZONE,
    CONF_WASTE_CODES,
    DOMAIN,
    WASTE_TYPES,
)
from .api import MantovaAmbienteAPI
from .coordinator import MantovaAmbienteCoordinator
from .models import RecyclingCollection

_LOGGER = logging.getLogger(__name__)


async def _get_zone_title(hass: HomeAssistant, zone_id: str) -> str:
    """Get the zone title from zone ID."""
    try:
        zones = await MantovaAmbienteAPI.async_get_zones(hass)
        for zone in zones:
            if zone["id"] == zone_id:
                return zone["title"]
    except Exception:
        _LOGGER.warning("Could not fetch zone title for ID %s", zone_id)
    
    return f"Zone {zone_id}"


def _get_waste_type_title(waste_code: str) -> str:
    """Get the waste type title from waste code."""
    return WASTE_TYPES.get(waste_code, f"Waste {waste_code}")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Mantova Ambiente sensor platform."""
    coordinator: MantovaAmbienteCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Get zone title
    zone_id = entry.data.get("zone", "")
    zone_title = await _get_zone_title(hass, zone_id)
    
    entities = []
    
    # Add tomorrow's waste sensor
    entities.append(TomorrowWasteSensor(coordinator, entry, zone_title))
    
    # Add individual waste type sensors
    waste_codes = entry.data.get(CONF_WASTE_CODES, [])
    if isinstance(waste_codes, str):
        waste_codes = [code.strip() for code in waste_codes.split(",") if code.strip()]
    
    for waste_code in waste_codes:
        waste_title = _get_waste_type_title(waste_code)
        entities.append(WasteTypeSensor(coordinator, entry, waste_code, waste_title, zone_title))
    
    async_add_entities(entities, True)


class MantovaAmbienteEntity(CoordinatorEntity[MantovaAmbienteCoordinator]):
    """Base entity for Mantova Ambiente integration."""
    
    def __init__(
        self,
        coordinator: MantovaAmbienteCoordinator,
        entry: ConfigEntry,
        zone_title: str = None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._zone = entry.data.get("zone", "")
        self._zone_title = zone_title or f"Zone {self._zone}"
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return common state attributes."""
        attrs = {
            ATTR_ZONE: self._zone,
        }
        
        if self.coordinator.data:
            attrs["last_update"] = self.coordinator.data.last_update.isoformat()
        
        return attrs


class TomorrowWasteSensor(MantovaAmbienteEntity, SensorEntity):
    """Sensor for tomorrow's waste collection."""
    
    def __init__(
        self,
        coordinator: MantovaAmbienteCoordinator,
        entry: ConfigEntry,
        zone_title: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, zone_title)
        self._attr_name = f"Mantova Ambiente Tomorrow Waste {zone_title}"
        self._attr_unique_id = f"mantova_ambiente_tomorrow_{self._zone}"
        self._attr_icon = "mdi:delete-variant"
    
    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return "unknown"
        
        tomorrow_collections = self.coordinator.data.get_tomorrow_collections()
        
        if not tomorrow_collections:
            return "none"
        
        # Return comma-separated list of waste types for tomorrow
        waste_types = [collection.title for collection in tomorrow_collections]
        return ", ".join(waste_types)
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = super().extra_state_attributes
        
        if self.coordinator.data:
            tomorrow_collections = self.coordinator.data.get_tomorrow_collections()
            
            attrs["count"] = len(tomorrow_collections)
            attrs["collections"] = [
                {
                    "id": collection.id,
                    "title": collection.title,
                    "dates": [dt.isoformat() for dt in collection.collections]
                }
                for collection in tomorrow_collections
            ]
        
        return attrs


class WasteTypeSensor(MantovaAmbienteEntity, BinarySensorEntity):
    """Sensor for individual waste type."""
    
    def __init__(
        self,
        coordinator: MantovaAmbienteCoordinator,
        entry: ConfigEntry,
        waste_code: str,
        waste_title: str,
        zone_title: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry, zone_title)
        self._waste_code = waste_code
        self._waste_title = waste_title
        self._attr_name = f"Mantova Ambiente Waste {waste_title} {zone_title}"
        self._attr_unique_id = f"mantova_ambiente_waste_{waste_code}_{self._zone}"
        self._attr_icon = "mdi:recycle"
    
    @property
    def is_on(self) -> bool:
        """Return True if this waste type is collected tomorrow."""
        if not self.coordinator.data:
            return False
        
        collection = self.coordinator.data.get_collection_by_id(self._waste_code)
        if not collection:
            return False
        
        return collection.is_collection_tomorrow()
    
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        attrs = super().extra_state_attributes
        attrs[ATTR_WASTE_TYPE] = self._waste_code
        attrs["waste_title"] = self._waste_title
        
        if self.coordinator.data:
            collection = self.coordinator.data.get_collection_by_id(self._waste_code)
            if collection:
                attrs["title"] = collection.title
                attrs[ATTR_NEXT_DATES] = [
                    dt.isoformat() for dt in collection.next_collections
                ]
            else:
                attrs["title"] = self._waste_title
                attrs[ATTR_NEXT_DATES] = []
        
        return attrs