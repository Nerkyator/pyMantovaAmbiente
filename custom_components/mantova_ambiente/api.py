"""API service for Mantova Ambiente integration."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import API_BASE_URL, API_ZONES_URL, API_TIMEOUT
from .models import MantovaAmbienteData, RecyclingCollection

_LOGGER = logging.getLogger(__name__)


class MantovaAmbienteAPI:
    """API client for Mantova Ambiente service."""
    
    def __init__(self, hass: HomeAssistant, zone: str, cache_hours: int = 24):
        """Initialize the API client."""
        self.hass = hass
        self.zone = zone
        self.cache_hours = cache_hours
        self._session = async_get_clientsession(hass)
        
        # Cache setup
        self.cache_dir = hass.config.path("custom_components", "mantova_ambiente", "cache")
        self.cache_file = os.path.join(self.cache_dir, f"collections_{zone}.json")
        
        # Create cache directory synchronously in __init__ (it's a one-time setup)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def async_get_data(self, force_refresh: bool = False) -> MantovaAmbienteData:
        """Get waste collection data, using cache when available."""
        try:
            # Try cache first
            if not force_refresh:
                cached_data = await self._async_get_cached_data()
                if cached_data:
                    _LOGGER.debug("Using cached data for zone %s", self.zone)
                    return cached_data
            
            # Fetch from API
            _LOGGER.info("Fetching data from Mantova Ambiente API for zone %s", self.zone)
            raw_data = await self._async_fetch_from_api()
            
            # Parse response
            collections = await self._async_parse_api_response(raw_data)
            
            # Create data container
            data = MantovaAmbienteData(
                collections=collections,
                last_update=datetime.now()
            )
            
            # Cache the data
            await self._async_cache_data(data)
            
            _LOGGER.info("Successfully fetched %d collections for zone %s", 
                        len(collections), self.zone)
            
            return data
            
        except Exception as e:
            _LOGGER.error("Error getting data for zone %s: %s", self.zone, str(e))
            # Try to return cached data as fallback
            cached_data = await self._async_get_cached_data(ignore_expiry=True)
            if cached_data:
                _LOGGER.warning("Using expired cached data as fallback for zone %s", self.zone)
                return cached_data
            raise
    
    async def _async_fetch_from_api(self) -> List[Dict[str, Any]]:
        """Fetch data from the Mantova Ambiente API."""
        url = f"{API_BASE_URL}?zone={self.zone}&from=today"
        
        try:
            async with self._session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
            ) as response:
                if response.status != 200:
                    raise Exception(f"API returned status {response.status}")
                
                response_data = await response.json()
                
                # API returns an object with 'data' containing the array
                if 'data' in response_data:
                    data = response_data['data']
                else:
                    data = response_data
                
                _LOGGER.debug("API response received: %d collections", len(data))
                return data
                
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}") from e
        except Exception as e:
            raise Exception(f"API error: {str(e)}") from e
    
    async def _async_parse_api_response(self, data: List[Dict[str, Any]]) -> List[RecyclingCollection]:
        """Parse API response into RecyclingCollection objects."""
        collections = []
        
        for item in data:
            try:
                # Parse collection dates
                collection_dates = []
                collections_data = item.get("collections", [])
                
                if not collections_data:
                    continue
                
                for date_str in collections_data:
                    try:
                        # Parse date string to datetime
                        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                        collection_dates.append(dt)
                    except ValueError as e:
                        _LOGGER.warning("Could not parse date '%s': %s", date_str, e)
                        continue
                
                if not collection_dates:
                    continue
                
                collection = RecyclingCollection(
                    id=str(item.get("id", "")),
                    title=item.get("title", ""),
                    collections=collection_dates
                )
                collections.append(collection)
                
            except Exception as e:
                _LOGGER.warning("Could not parse collection item: %s", e)
                continue
        
        return collections
    
    async def _async_get_cached_data(self, ignore_expiry: bool = False) -> MantovaAmbienteData | None:
        """Get cached data if available and not expired."""
        try:
            # Use executor for os.path.exists to avoid blocking
            cache_exists = await self.hass.async_add_executor_job(os.path.exists, self.cache_file)
            if not cache_exists:
                return None
            
            # Check cache age
            if not ignore_expiry:
                cache_mtime = await self.hass.async_add_executor_job(os.path.getmtime, self.cache_file)
                cache_age = (datetime.now().timestamp() - cache_mtime) / 3600
                
                if cache_age > self.cache_hours:
                    _LOGGER.debug("Cache expired (%.1fh > %dh)", cache_age, self.cache_hours)
                    return None
            
            # Load cached data
            def _read_cache_file():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            cache_data = await self.hass.async_add_executor_job(_read_cache_file)
            
            # Parse cached collections
            collections = []
            for item in cache_data["collections"]:
                # Parse datetime strings back to datetime objects
                collection_dates = [
                    datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    for date_str in item["collections"]
                ]
                
                collection = RecyclingCollection(
                    id=item["id"],
                    title=item["title"],
                    collections=collection_dates
                )
                collections.append(collection)
            
            return MantovaAmbienteData(
                collections=collections,
                last_update=datetime.fromisoformat(cache_data["last_update"])
            )
            
        except Exception as e:
            _LOGGER.warning("Could not load cached data: %s", e)
            return None
    
    async def _async_cache_data(self, data: MantovaAmbienteData) -> None:
        """Cache the fetched data."""
        try:
            # Convert to serializable format
            cache_data = {
                "last_update": data.last_update.isoformat(),
                "collections": []
            }
            
            for collection in data.collections:
                cache_data["collections"].append({
                    "id": collection.id,
                    "title": collection.title,
                    "collections": [dt.isoformat() for dt in collection.collections]
                })
            
            # Write to cache file
            def _write_cache_file():
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            await self.hass.async_add_executor_job(_write_cache_file)
            
            _LOGGER.debug("Data cached successfully for zone %s", self.zone)
            
        except Exception as e:
            _LOGGER.error("Could not cache data: %s", e)
    
    @staticmethod
    async def async_get_zones(hass: HomeAssistant) -> List[Dict[str, str]]:
        """Get available zones from the Mantova Ambiente API."""
        session = async_get_clientsession(hass)
        
        try:
            async with session.get(
                API_ZONES_URL,
                timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
            ) as response:
                if response.status != 200:
                    raise Exception(f"API returned status {response.status}")
                
                response_data = await response.json()
                
                # API returns an object with 'data' containing the array
                if 'data' in response_data:
                    zones_data = response_data['data']
                else:
                    zones_data = response_data
                
                # Return list of dicts with id and title
                zones = [{"id": zone["id"], "title": zone["title"]} for zone in zones_data]
                
                _LOGGER.debug("Retrieved %d zones from API", len(zones))
                return zones
                
        except aiohttp.ClientError as e:
            _LOGGER.error("HTTP error while fetching zones: %s", e)
            raise
        except Exception as e:
            _LOGGER.error("Error fetching zones: %s", e)
            raise