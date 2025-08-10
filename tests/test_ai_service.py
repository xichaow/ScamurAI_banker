"""
Unit tests for AI service functionality.

Tests OpenAI integration, error handling, and response parsing.
Note: Tests use mocking to avoid requiring actual OpenAI API calls.
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.ai_service import OpenAIService, OpenAIError

class TestOpenAIService:
    """Test cases for OpenAIService."""
    
    def test_initialization_success(self):
        """Test successful service initialization."""
        service = OpenAIService(api_key="test_key")
        assert service.api_key == "test_key"
        assert service.model == "gpt-3.5-turbo"
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key raises error."""
        with pytest.raises(OpenAIError):
            OpenAIService(api_key=None)
        
        with pytest.raises(OpenAIError):
            OpenAIService(api_key="your_openai_api_key_here")
    
    def test_json_response_parsing_valid(self):
        """Test parsing valid JSON responses."""
        service = OpenAIService(api_key="test_key")
        
        json_response = '{"summary": "test", "questions": ["Q1"], "risk_level": "Medium"}'
        result = service._parse_json_response(json_response)
        
        assert result["summary"] == "test"
        assert result["questions"] == ["Q1"]
        assert result["risk_level"] == "Medium"
    
    def test_json_response_parsing_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        service = OpenAIService(api_key="test_key")
        
        markdown_response = '''```json
        {"summary": "test", "questions": ["Q1"], "risk_level": "Low"}
        ```'''
        
        result = service._parse_json_response(markdown_response)
        assert result["summary"] == "test"
    
    def test_json_response_parsing_invalid(self):
        """Test parsing invalid JSON returns fallback."""
        service = OpenAIService(api_key="test_key")
        
        invalid_json = "This is not JSON"
        result = service._parse_json_response(invalid_json)
        
        assert "error" in result
        assert "questions" in result
        assert isinstance(result["questions"], list)
        assert len(result["questions"]) >= 5
    
    def test_token_usage_tracking(self):
        """Test token usage tracking."""
        service = OpenAIService(api_key="test_key")
        
        # Test initial state
        initial_usage = service.get_usage_stats()
        assert initial_usage["token_usage"]["total_tokens"] == 0
        
        # Test usage update
        service._update_token_usage({"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50})
        
        updated_usage = service.get_usage_stats()
        assert updated_usage["token_usage"]["total_tokens"] == 100
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        service = OpenAIService(api_key="test_key")
        service.min_request_interval = 0.1  # Shorter for testing
        
        import time
        start_time = time.time()
        
        # First call should be immediate
        await service._rate_limit()
        first_call_time = time.time()
        
        # Second call should be delayed
        await service._rate_limit()
        second_call_time = time.time()
        
        # Should have at least the minimum interval between calls
        assert second_call_time - first_call_time >= 0.1
    
    @pytest.mark.asyncio
    @patch('src.services.ai_service.AsyncOpenAI')
    async def test_analyze_fraud_data_success(self, mock_openai_class):
        """Test successful fraud data analysis."""
        # Mock OpenAI client
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"summary": "Analysis complete", "questions": ["Q1", "Q2", "Q3", "Q4", "Q5"], "risk_level": "Medium"}'
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 100
        mock_response.usage.prompt_tokens = 60
        mock_response.usage.completion_tokens = 40
        
        mock_client.chat.completions.create.return_value = mock_response
        
        service = OpenAIService(api_key="test_key")
        service.client = mock_client
        
        result = await service.analyze_fraud_data("12345", "test data")
        
        assert result["summary"] == "Analysis complete"
        assert len(result["questions"]) == 5
        assert result["risk_level"] == "Medium"
    
    @pytest.mark.asyncio
    @patch('src.services.ai_service.AsyncOpenAI')
    async def test_analyze_fraud_data_failure(self, mock_openai_class):
        """Test fraud data analysis with API failure."""
        # Mock OpenAI client to raise exception
        mock_client = AsyncMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        service = OpenAIService(api_key="test_key")
        service.client = mock_client
        
        result = await service.analyze_fraud_data("12345", "test data")
        
        # Should return fallback response
        assert "error" in result
        assert "questions" in result
        assert len(result["questions"]) >= 5
    
    @pytest.mark.asyncio
    async def test_generate_followup_questions(self):
        """Test follow-up question generation."""
        service = OpenAIService(api_key="test_key")
        
        with patch.object(service, '_make_completion_request') as mock_request:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = '["Question 1?", "Question 2?", "Question 3?"]'
            mock_request.return_value = mock_response
            
            result = await service.generate_followup_questions("12345", "Previous analysis", "Context")
            
            assert isinstance(result, list)
            assert len(result) == 3
            assert all("Question" in q for q in result)
    
    def test_get_usage_stats(self):
        """Test usage statistics retrieval."""
        service = OpenAIService(api_key="test_key")
        
        stats = service.get_usage_stats()
        
        assert "token_usage" in stats
        assert "model" in stats
        assert "api_configured" in stats
        assert stats["model"] == "gpt-3.5-turbo"
        assert stats["api_configured"] is True
    
    @pytest.mark.asyncio
    async def test_connection_test_success(self):
        """Test successful connection test."""
        service = OpenAIService(api_key="test_key")
        
        with patch.object(service, '_make_completion_request') as mock_request:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello"
            mock_request.return_value = mock_response
            
            result = await service.test_connection()
            
            assert result["status"] == "success"
            assert result["response_received"] is True
    
    @pytest.mark.asyncio
    async def test_connection_test_failure(self):
        """Test connection test with failure."""
        service = OpenAIService(api_key="test_key")
        
        with patch.object(service, '_make_completion_request') as mock_request:
            mock_request.side_effect = Exception("Connection failed")
            
            result = await service.test_connection()
            
            assert result["status"] == "error"
            assert "Connection failed" in result["error"]

if __name__ == '__main__':
    pytest.main([__file__])