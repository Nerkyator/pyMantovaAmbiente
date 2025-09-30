"""Tests for Mantova Ambiente models."""
from datetime import datetime, timedelta

import pytest

from custom_components.mantova_ambiente.models import MantovaAmbienteData, RecyclingCollection


class TestRecyclingCollection:
    """Test RecyclingCollection model."""
    
    def test_recycling_collection_creation(self):
        """Test creating a RecyclingCollection."""
        collection = RecyclingCollection(
            id="3707",
            title="Organic Waste",
            collections=[
                datetime(2025, 10, 5, 6, 0, 0),
                datetime(2025, 10, 1, 6, 0, 0),
                datetime(2025, 10, 3, 6, 0, 0),
            ]
        )
        
        assert collection.id == "3707"
        assert collection.title == "Organic Waste"
        assert len(collection.collections) == 3
        
        # Should be sorted after __post_init__
        assert collection.collections[0] == datetime(2025, 10, 1, 6, 0, 0)
        assert collection.collections[1] == datetime(2025, 10, 3, 6, 0, 0)
        assert collection.collections[2] == datetime(2025, 10, 5, 6, 0, 0)
    
    def test_next_collection(self):
        """Test next_collection property."""
        now = datetime(2025, 9, 30, 12, 0, 0)
        
        collection = RecyclingCollection(
            id="3707",
            title="Organic Waste",
            collections=[
                datetime(2025, 9, 29, 6, 0, 0),  # Past
                datetime(2025, 10, 1, 6, 0, 0),  # Future
                datetime(2025, 10, 3, 6, 0, 0),  # Future
            ]
        )
        
        # Mock datetime.now() to return fixed date
        with pytest.mock.patch('custom_components.mantova_ambiente.models.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            next_collection = collection.next_collection
            assert next_collection == datetime(2025, 10, 1, 6, 0, 0)
    
    def test_next_collections(self):
        """Test next_collections property."""
        now = datetime(2025, 9, 30, 12, 0, 0)
        
        collection = RecyclingCollection(
            id="3707",
            title="Organic Waste",
            collections=[
                datetime(2025, 9, 29, 6, 0, 0),  # Past
                datetime(2025, 10, 1, 6, 0, 0),  # Future
                datetime(2025, 10, 3, 6, 0, 0),  # Future
            ]
        )
        
        with pytest.mock.patch('custom_components.mantova_ambiente.models.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            next_collections = collection.next_collections
            assert len(next_collections) == 2
            assert next_collections[0] == datetime(2025, 10, 1, 6, 0, 0)
            assert next_collections[1] == datetime(2025, 10, 3, 6, 0, 0)
    
    def test_is_collection_tomorrow(self):
        """Test is_collection_tomorrow method."""
        # Test on September 30th (edge case)
        now = datetime(2025, 9, 30, 12, 0, 0)
        
        collection = RecyclingCollection(
            id="3707",
            title="Organic Waste",
            collections=[
                datetime(2025, 9, 29, 6, 0, 0),   # Yesterday
                datetime(2025, 10, 1, 6, 0, 0),   # Tomorrow (October 1st)
                datetime(2025, 10, 2, 6, 0, 0),   # Day after tomorrow
            ]
        )
        
        with pytest.mock.patch('custom_components.mantova_ambiente.models.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            
            assert collection.is_collection_tomorrow() is True
        
        # Test with no tomorrow collection
        collection_no_tomorrow = RecyclingCollection(
            id="3708",
            title="Paper Waste",
            collections=[
                datetime(2025, 9, 29, 6, 0, 0),   # Yesterday
                datetime(2025, 10, 2, 6, 0, 0),   # Day after tomorrow
            ]
        )
        
        with pytest.mock.patch('custom_components.mantova_ambiente.models.datetime') as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
            # Need to also mock timedelta since we're using it now
            mock_datetime.timedelta = timedelta
            
            assert collection_no_tomorrow.is_collection_tomorrow() is False


class TestMantovaAmbienteData:
    """Test MantovaAmbienteData model."""
    
    def test_get_collection_by_id(self, mock_recycling_collections):
        """Test get_collection_by_id method."""
        data = MantovaAmbienteData(
            collections=mock_recycling_collections,
            last_update=datetime.now()
        )
        
        # Test existing ID
        collection = data.get_collection_by_id("3707")
        assert collection is not None
        assert collection.id == "3707"
        assert collection.title == "Organic Waste"
        
        # Test non-existing ID
        collection = data.get_collection_by_id("9999")
        assert collection is None
    
    def test_get_tomorrow_collections(self, mock_recycling_collections):
        """Test get_tomorrow_collections method."""
        data = MantovaAmbienteData(
            collections=mock_recycling_collections,
            last_update=datetime.now()
        )
        
        # Mock the is_collection_tomorrow method to return True for first collection
        with pytest.mock.patch.object(mock_recycling_collections[0], 'is_collection_tomorrow', return_value=True), \
             pytest.mock.patch.object(mock_recycling_collections[1], 'is_collection_tomorrow', return_value=False), \
             pytest.mock.patch.object(mock_recycling_collections[2], 'is_collection_tomorrow', return_value=True):
            
            tomorrow_collections = data.get_tomorrow_collections()
            assert len(tomorrow_collections) == 2
            assert tomorrow_collections[0].id == "3707"
            assert tomorrow_collections[1].id == "3710"