"""Tests for Mantova Ambiente API client."""
import json
from datetime import datetime
from unittest.mock import AsyncMock, mock_open, patch

import pytest
import aiohttp
from homeassistant.core import HomeAssistant

from custom_components.mantova_ambiente.api import MantovaAmbienteAPI
from custom_components.mantova_ambiente.models import MantovaAmbienteData


class TestMantovaAmbienteAPI:
    """Test MantovaAmbienteAPI class."""
    
    @pytest.fixture
    def api_client(self, hass: HomeAssistant):
        """Create API client for testing."""
        return MantovaAmbienteAPI(hass, "3631", 24)
    
    @pytest.mark.asyncio
    async def test_fetch_from_api_success(self, api_client, mock_api_response):
        """Test successful API fetch."""
        with patch.object(api_client._session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value=mock_api_response)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await api_client._async_fetch_from_api()
            
            assert result == mock_api_response["data"]
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_from_api_http_error(self, api_client):
        """Test API fetch with HTTP error."""
        with patch.object(api_client._session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 404
            mock_get.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(Exception, match="API returned status 404"):
                await api_client._async_fetch_from_api()
    
    @pytest.mark.asyncio
    async def test_fetch_from_api_network_error(self, api_client):
        """Test API fetch with network error."""
        with patch.object(api_client._session, 'get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Network error")
            
            with pytest.raises(Exception, match="Network error"):
                await api_client._async_fetch_from_api()
    
    @pytest.mark.asyncio
    async def test_parse_api_response(self, api_client, mock_api_response):
        """Test parsing API response."""
        collections = await api_client._async_parse_api_response(mock_api_response["data"])
        
        assert len(collections) == 3
        assert collections[0].id == "3707"
        assert collections[0].title == "Organic Waste"
        assert len(collections[0].collections) == 3
        assert collections[0].collections[0] == datetime(2025, 10, 1, 6, 0, 0)
    
    @pytest.mark.asyncio
    async def test_parse_api_response_invalid_date(self, api_client):
        """Test parsing API response with invalid date."""
        invalid_data = [{
            "id": "3707",
            "title": "Organic Waste",
            "collections": ["invalid-date", "2025-10-01 06:00:00"]
        }]
        
        collections = await api_client._async_parse_api_response(invalid_data)
        
        assert len(collections) == 1
        assert len(collections[0].collections) == 1  # Only valid date parsed
    
    @pytest.mark.asyncio
    async def test_cache_data(self, api_client, mock_mantova_ambiente_data, mock_cache_file_content):
        """Test caching data."""
        with patch("builtins.open", mock_open()) as mock_file, \
             patch("json.dump") as mock_json_dump, \
             patch("os.makedirs"):
            
            await api_client._async_cache_data(mock_mantova_ambiente_data)
            
            mock_file.assert_called_once()
            mock_json_dump.assert_called_once()
            
            # Check that the correct data structure was passed to json.dump
            call_args = mock_json_dump.call_args[0]
            cached_data = call_args[0]
            
            assert "last_update" in cached_data
            assert "collections" in cached_data
            assert len(cached_data["collections"]) == 3
    
    @pytest.mark.asyncio
    async def test_get_cached_data_success(self, api_client, mock_cache_file_content):
        """Test loading cached data successfully."""
        with patch("os.path.exists", return_value=True), \
             patch("os.path.getmtime", return_value=datetime.now().timestamp() - 3600), \
             patch("builtins.open", mock_open(read_data=json.dumps(mock_cache_file_content))):
            
            cached_data = await api_client._async_get_cached_data()
            
            assert cached_data is not None
            assert isinstance(cached_data, MantovaAmbienteData)
            assert len(cached_data.collections) == 3
    
    @pytest.mark.asyncio
    async def test_get_cached_data_expired(self, api_client):
        """Test loading expired cached data."""
        expired_time = datetime.now().timestamp() - (25 * 3600)  # 25 hours ago
        
        with patch("os.path.exists", return_value=True), \
             patch("os.path.getmtime", return_value=expired_time):
            
            cached_data = await api_client._async_get_cached_data()
            
            assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_get_cached_data_no_file(self, api_client):
        """Test loading cached data when file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            cached_data = await api_client._async_get_cached_data()
            assert cached_data is None
    
    @pytest.mark.asyncio
    async def test_get_data_with_cache(self, api_client, mock_mantova_ambiente_data):
        """Test getting data with cache hit."""
        with patch.object(api_client, '_async_get_cached_data', return_value=mock_mantova_ambiente_data):
            result = await api_client.async_get_data()
            
            assert result == mock_mantova_ambiente_data
    
    @pytest.mark.asyncio
    async def test_get_data_cache_miss(self, api_client, mock_api_response, mock_mantova_ambiente_data):
        """Test getting data with cache miss."""
        with patch.object(api_client, '_async_get_cached_data', return_value=None), \
             patch.object(api_client, '_async_fetch_from_api', return_value=mock_api_response["data"]), \
             patch.object(api_client, '_async_parse_api_response', return_value=mock_mantova_ambiente_data.collections), \
             patch.object(api_client, '_async_cache_data') as mock_cache:
            
            result = await api_client.async_get_data()
            
            assert isinstance(result, MantovaAmbienteData)
            assert len(result.collections) == 3
            mock_cache.assert_called_once()