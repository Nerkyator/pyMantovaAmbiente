"""Config flow for Mantova Ambiente integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import MantovaAmbienteAPI
from .const import (
    CONF_CACHE_HOURS,
    CONF_WASTE_CODES,
    CONF_ZONE,
    DEFAULT_CACHE_HOURS,
    DOMAIN,
    WASTE_TYPES,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Mantova Ambiente."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self._zones = []
        self._selected_zone_id = None
        self._selected_zone_title = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the zone selection step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            self._selected_zone_id = user_input[CONF_ZONE]
            # Find the zone title
            for zone in self._zones:
                if zone["id"] == self._selected_zone_id:
                    self._selected_zone_title = zone["title"]
                    break
            
            return await self.async_step_waste_types()

        # Load zones from API
        try:
            self._zones = await MantovaAmbienteAPI.async_get_zones(self.hass)
        except Exception:
            _LOGGER.exception("Error loading zones")
            errors["base"] = "cannot_connect"
            self._zones = []

        if not self._zones:
            return self.async_abort(reason="no_zones")

        # Create zone selection schema
        zone_options = {zone["id"]: zone["title"] for zone in self._zones}
        
        data_schema = vol.Schema({
            vol.Required(CONF_ZONE): vol.In(zone_options),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_waste_types(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the waste types selection step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            selected_waste_codes = []
            
            # Extract selected waste codes from checkboxes
            for waste_id in WASTE_TYPES.keys():
                if user_input.get(f"waste_{waste_id}", False):
                    selected_waste_codes.append(waste_id)
            
            if not selected_waste_codes:
                errors["base"] = "no_waste_types_selected"
            else:
                # Prepare final configuration data
                config_data = {
                    CONF_ZONE: self._selected_zone_id,
                    CONF_CACHE_HOURS: user_input.get(CONF_CACHE_HOURS, DEFAULT_CACHE_HOURS),
                    CONF_WASTE_CODES: selected_waste_codes,
                }
                
                # Test the API connection
                try:
                    api = MantovaAmbienteAPI(self.hass, config_data[CONF_ZONE], config_data[CONF_CACHE_HOURS])
                    await api.async_get_data()
                except Exception:
                    _LOGGER.exception("Cannot connect to Mantova Ambiente API")
                    errors["base"] = "cannot_connect"
                else:
                    # Create unique ID based on zone
                    await self.async_set_unique_id(self._selected_zone_id)
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(
                        title=f"Mantova Ambiente - {self._selected_zone_title}",
                        data=config_data
                    )

        # Create waste types selection schema with checkboxes
        waste_schema = {}
        for waste_id, waste_title in WASTE_TYPES.items():
            waste_schema[vol.Optional(f"waste_{waste_id}", default=False)] = bool
        
        # Add cache hours option
        waste_schema[vol.Optional(CONF_CACHE_HOURS, default=DEFAULT_CACHE_HOURS)] = vol.All(
            vol.Coerce(int), vol.Range(min=1, max=168)
        )
        
        data_schema = vol.Schema(waste_schema)

        return self.async_show_form(
            step_id="waste_types",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "zone_title": self._selected_zone_title,
            },
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class NoZones(HomeAssistantError):
    """Error to indicate no zones were found."""


class NoWasteTypesSelected(HomeAssistantError):
    """Error to indicate no waste types were selected."""