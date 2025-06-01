"""
Unit tests for the DestinationService.
Tests business logic, error handling, and API interactions.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.services import DestinationService, DestinationGenerationError
from src.models import GenerationRequest, ThemeType, Destination, Activity


class TestDestinationService:
    """Test suite for DestinationService."""
    
    @pytest.fixture
    def service(self):
        """Create a DestinationService instance for testing."""
        with patch('src.services.destination_service.OpenAI'):
            return DestinationService()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample GenerationRequest for testing."""
        return GenerationRequest(
            theme=ThemeType.SPORTS,
            count=3,
            include_activities=True
        )
    
    @pytest.fixture
    def mock_destination_response(self):
        """Mock API response for destinations."""
        return {
            "destinations": '{"destinations": [{"place": "Test Place", "country": "Test Country", "description": "Test description", "best_time_to_visit": "Year-round", "coordinates": {"lat": 0.0, "lng": 0.0}, "rating": 4.5}]}'
        }
    
    @pytest.fixture
    def mock_activity_response(self):
        """Mock API response for activities."""
        return {
            "activities": '{"activities": [{"name": "Test Activity", "description": "Test activity description", "activity_type": "Outdoor", "duration_hours": 2.0, "difficulty_level": 3, "cost_estimate": "Moderate"}]}'
        }
    
    @pytest.mark.asyncio
    async def test_generate_destinations_success(self, service, sample_request, mock_destination_response, mock_activity_response):
        """Test successful destination generation."""
        # Mock the chain responses
        service.destination_chain = AsyncMock(return_value=mock_destination_response)
        service.activity_chain = AsyncMock(return_value=mock_activity_response)
        
        # Mock the safe API request method
        service._safe_api_request = AsyncMock()
        service._safe_api_request.side_effect = [
            mock_destination_response,
            mock_activity_response
        ]
        
        response = await service.generate_destinations(sample_request)
        
        assert response is not None
        assert response.theme == ThemeType.SPORTS
        assert len(response.destinations) > 0
        assert response.generation_time_seconds is not None
        assert response.generation_time_seconds > 0
    
    @pytest.mark.asyncio
    async def test_generate_destinations_api_error(self, service, sample_request):
        """Test handling of API errors during generation."""
        # Mock API failure
        service._safe_api_request = AsyncMock(side_effect=DestinationGenerationError("API Error"))
        
        with pytest.raises(DestinationGenerationError):
            await service.generate_destinations(sample_request)
    
    @pytest.mark.asyncio
    async def test_safe_api_request_retry_logic(self, service):
        """Test retry logic in safe API request."""
        mock_chain = Mock()
        mock_chain.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            {"success": "Third time works"}
        ]
        
        # Mock settings for faster testing
        with patch('src.services.destination_service.settings') as mock_settings:
            mock_settings.max_retries = 3
            mock_settings.retry_delay = 0.01
            
            result = await service._safe_api_request(mock_chain, {}, "test")
            assert result == {"success": "Third time works"}
    
    @pytest.mark.asyncio
    async def test_safe_api_request_max_retries_exceeded(self, service):
        """Test that max retries are respected."""
        mock_chain = Mock(side_effect=Exception("Persistent error"))
        
        with patch('src.services.destination_service.settings') as mock_settings:
            mock_settings.max_retries = 2
            mock_settings.retry_delay = 0.01
            
            with pytest.raises(DestinationGenerationError):
                await service._safe_api_request(mock_chain, {}, "test")
    
    def test_parse_json_response_valid_json(self, service):
        """Test parsing of valid JSON response."""
        valid_json = '{"destinations": [{"place": "Test", "country": "Country"}]}'
        result = service._parse_json_response(valid_json, "test")
        
        assert "destinations" in result
        assert len(result["destinations"]) == 1
        assert result["destinations"][0]["place"] == "Test"
    
    def test_parse_json_response_invalid_json(self, service):
        """Test fallback parsing for invalid JSON."""
        invalid_json = "Not valid JSON at all"
        result = service._parse_json_response(invalid_json, "destination generation")
        
        # Should fall back to basic parsing
        assert "destinations" in result
    
    def test_fallback_parse_destinations(self, service):
        """Test fallback parsing for destination responses."""
        text_response = "Paris, France\nTokyo, Japan\nNew York, USA"
        result = service._fallback_parse(text_response, "destination generation")
        
        assert "destinations" in result
        assert len(result["destinations"]) == 3
        assert result["destinations"][0]["place"] == "Paris"
        assert result["destinations"][0]["country"] == "France"
    
    def test_fallback_parse_activities(self, service):
        """Test fallback parsing for activity responses."""
        text_response = "Swimming\nHiking\nSightseeing"
        result = service._fallback_parse(text_response, "activity generation")
        
        assert "activities" in result
        assert len(result["activities"]) == 3
        assert result["activities"][0]["name"] == "Swimming"
    
    @pytest.mark.asyncio
    async def test_generate_activities_for_destination(self, service, mock_activity_response):
        """Test activity generation for a specific destination."""
        destination = Destination(
            place="Test Place",
            country="Test Country",
            theme=ThemeType.SPORTS,
            activities=[]
        )
        
        service._safe_api_request = AsyncMock(return_value=mock_activity_response)
        
        activities = await service._generate_activities_for_destination(destination, ThemeType.SPORTS)
        
        assert len(activities) > 0
        assert isinstance(activities[0], Activity)
    
    @pytest.mark.asyncio
    async def test_generate_activities_error_handling(self, service):
        """Test error handling in activity generation."""
        destination = Destination(
            place="Test Place",
            country="Test Country",
            theme=ThemeType.SPORTS,
            activities=[]
        )
        
        service._safe_api_request = AsyncMock(side_effect=Exception("API Error"))
        
        # Should return empty list on error, not raise exception
        activities = await service._generate_activities_for_destination(destination, ThemeType.SPORTS)
        assert activities == []
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, service, mock_destination_response):
        """Test successful health check."""
        service._safe_api_request = AsyncMock(return_value=mock_destination_response)
        
        # Mock the generate_destinations method to avoid complex setup
        service.generate_destinations = AsyncMock(return_value=Mock())
        
        result = await service.health_check()
        
        assert result["status"] == "healthy"
        assert "response_time_seconds" in result
        assert result["openai_connection"] == "ok"
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, service):
        """Test health check with service failure."""
        service.generate_destinations = AsyncMock(side_effect=Exception("Service down"))
        
        result = await service.health_check()
        
        assert result["status"] == "unhealthy"
        assert "error" in result
        assert result["openai_connection"] == "failed"
    
    def test_setup_chains(self, service):
        """Test that chains are properly initialized."""
        assert hasattr(service, 'destination_chain')
        assert hasattr(service, 'activity_chain')
        assert hasattr(service, 'destination_prompt')
        assert hasattr(service, 'activity_prompt')
    
    @pytest.mark.parametrize("theme", [theme for theme in ThemeType])
    async def test_all_themes_supported(self, service, theme, mock_destination_response):
        """Test that all theme types are supported."""
        request = GenerationRequest(
            theme=theme,
            count=1,
            include_activities=False
        )
        
        service._safe_api_request = AsyncMock(return_value=mock_destination_response)
        
        # Should not raise an exception for any theme
        response = await service.generate_destinations(request)
        assert response.theme == theme
    
    @pytest.mark.parametrize("count", [1, 5, 10])
    async def test_different_destination_counts(self, service, count, mock_destination_response):
        """Test generation with different destination counts."""
        request = GenerationRequest(
            theme=ThemeType.ENTERTAINMENT,
            count=count,
            include_activities=False
        )
        
        service._safe_api_request = AsyncMock(return_value=mock_destination_response)
        
        response = await service.generate_destinations(request)
        # The actual count might differ from requested due to API responses,
        # but should not raise an error
        assert isinstance(response.destinations, list) 