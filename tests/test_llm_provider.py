"""Tests for the LLM provider module."""
import os
import unittest
from unittest.mock import patch, MagicMock

from exceptions import APIKeyError, LLMProviderError
from agents.llm_provider import LLMFactory, CachingLLM, get_llm


class TestLLMFactory(unittest.TestCase):
    """Tests for the LLMFactory class."""
    
    def setUp(self):
        """Set up test environment."""
        # Save original environment variables
        self.original_openai_api_key = os.environ.get("OPENAI_API_KEY")
        self.original_anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        # Set environment variables for testing
        os.environ["OPENAI_API_KEY"] = "test-openai-api-key"
        os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-api-key"
    
    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment variables
        if self.original_openai_api_key:
            os.environ["OPENAI_API_KEY"] = self.original_openai_api_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)
            
        if self.original_anthropic_api_key:
            os.environ["ANTHROPIC_API_KEY"] = self.original_anthropic_api_key
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)
    
    def test_validate_api_key_openai(self):
        """Test API key validation for OpenAI."""
        # Should not raise an exception when API key is set
        LLMFactory.validate_api_key("gpt-turbo")
        
        # Remove API key and test for exception
        os.environ.pop("OPENAI_API_KEY", None)
        with self.assertRaises(APIKeyError):
            LLMFactory.validate_api_key("gpt-turbo")
    
    def test_validate_api_key_anthropic(self):
        """Test API key validation for Anthropic."""
        # Should not raise an exception when API key is set
        LLMFactory.validate_api_key("claude")
        
        # Remove API key and test for exception
        os.environ.pop("ANTHROPIC_API_KEY", None)
        with self.assertRaises(APIKeyError):
            LLMFactory.validate_api_key("claude")
    
    @patch("agents.llm_provider.ChatOpenAI")
    def test_create_llm_openai(self, mock_chat_openai):
        """Test creating an OpenAI LLM."""
        # Setup mock
        mock_instance = MagicMock()
        mock_chat_openai.return_value = mock_instance
        
        # Call method
        llm = LLMFactory.create_llm("gpt-turbo", "gpt-3.5-turbo")
        
        # Assertions
        self.assertEqual(llm, mock_instance)
        mock_chat_openai.assert_called_once()
    
    @patch("agents.llm_provider.ChatAnthropic")
    def test_create_llm_claude(self, mock_chat_anthropic):
        """Test creating a Claude LLM."""
        # Setup mock
        mock_instance = MagicMock()
        mock_chat_anthropic.return_value = mock_instance
        
        # Call method
        llm = LLMFactory.create_llm("claude", "claude-instant-1")
        
        # Assertions
        self.assertEqual(llm, mock_instance)
        mock_chat_anthropic.assert_called_once()
    
    def test_create_llm_unsupported(self):
        """Test creating an unsupported LLM."""
        with self.assertRaises(LLMProviderError):
            LLMFactory.create_llm("unsupported", "model")


class TestCachingLLM(unittest.TestCase):
    """Tests for the CachingLLM class."""
    
    def setUp(self):
        """Set up test environment."""
        self.mock_llm = MagicMock()
        self.caching_llm = CachingLLM(self.mock_llm)
    
    @patch("agents.llm_provider.CachingLLM._cached_call")
    async def test_acall_cached(self, mock_cached_call):
        """Test acall with cached response."""
        # Setup mock
        mock_cached_call.return_value = "cached response"
        
        # Create mock message
        mock_message = MagicMock()
        mock_message.content = "test message"
        
        # Call method
        response = await self.caching_llm.acall([mock_message])
        
        # Assertions
        self.assertEqual(response.content, "cached response")
        mock_cached_call.assert_called_once_with("test message")
    
    @patch("agents.llm_provider.time.sleep")
    async def test_acall_retry(self, mock_sleep):
        """Test acall with retry."""
        # Setup mock to fail on first attempt
        self.mock_llm.acall.side_effect = [
            Exception("Test exception"),
            MagicMock(content="success")
        ]
        
        # Create mock messages (multiple to bypass cache)
        mock_message1 = MagicMock()
        mock_message1.content = "test message 1"
        mock_message2 = MagicMock()
        mock_message2.content = "test message 2"
        
        # Call method
        response = await self.caching_llm.acall([mock_message1, mock_message2])
        
        # Assertions
        self.assertEqual(response.content, "success")
        self.assertEqual(self.mock_llm.acall.call_count, 2)
        mock_sleep.assert_called_once()


@patch("agents.llm_provider.settings")
@patch("agents.llm_provider.LLMFactory.create_llm")
class TestGetLLM(unittest.TestCase):
    """Tests for the get_llm function."""
    
    def test_get_llm_with_agent_type(self, mock_create_llm, mock_settings):
        """Test get_llm with agent type."""
        # Setup mocks
        mock_settings.get.return_value = {
            "research": {
                "provider": "gpt-turbo",
                "model": "gpt-3.5-turbo"
            }
        }
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm
        
        # Call function
        result = get_llm("research")
        
        # Assertions
        self.assertIsInstance(result, CachingLLM)
        self.assertEqual(result.llm, mock_llm)
        mock_create_llm.assert_called_once_with("gpt-turbo", "gpt-3.5-turbo", 0.0)
    
    def test_get_llm_without_agent_type(self, mock_create_llm, mock_settings):
        """Test get_llm without agent type."""
        # Setup mocks
        mock_settings.get.return_value = {
            "default": {
                "provider": "claude",
                "model": "claude-instant-1",
                "temperature": 0.2
            }
        }
        mock_llm = MagicMock()
        mock_create_llm.return_value = mock_llm
        
        # Call function
        result = get_llm()
        
        # Assertions
        self.assertIsInstance(result, CachingLLM)
        self.assertEqual(result.llm, mock_llm)
        mock_create_llm.assert_called_once_with("claude", "claude-instant-1", 0.2)


if __name__ == "__main__":
    unittest.main()