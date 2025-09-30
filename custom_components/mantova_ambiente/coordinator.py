"""DataUpdateCoordinator for Mantova Ambiente integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MantovaAmbienteAPI
from .const import CONF_CACHE_HOURS, CONF_ZONE, DEFAULT_SCAN_INTERVAL
from .models import MantovaAmbienteData

_LOGGER = logging.getLogger(__name__)


class MantovaAmbienteCoordinator(DataUpdateCoordinator[MantovaAmbienteData]):
    """Class to manage fetching Mantova Ambiente data."""
    
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        self.entry = entry
        self.zone = entry.data[CONF_ZONE]
        self.cache_hours = entry.data.get(CONF_CACHE_HOURS, 24)
        
        self.api = MantovaAmbienteAPI(hass, self.zone, self.cache_hours)
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"Mantova Ambiente {self.zone}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
    
    async def _async_update_data(self) -> MantovaAmbienteData:
        """Fetch data from API endpoint."""
        try:
            return await self.api.async_get_data()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
    
    async def async_force_refresh(self) -> None:
        """Force a refresh of the data."""
        try:
            data = await self.api.async_get_data(force_refresh=True)
            self.async_set_updated_data(data)
        except Exception as err:
            _LOGGER.error("Error during forced refresh: %s", err)
            raise UpdateFailed(f"Error during forced refresh: {err}") from err