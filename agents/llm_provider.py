"""LLM provider module for the exporter-agent."""
import os
import time
from functools import lru_cache
from typing import Dict, Any, Optional

from langchain.schema import BaseMessage
from langchain.chat_models.base import BaseChatModel

from config import settings
from exceptions import APIKeyError, LLMProviderError
from logging_utils import get_logger

logger = get_logger()

class LLMFactory:
    """Factory class for creating LLM instances."""
    
    @staticmethod
    def validate_api_key(provider: str) -> None:
        """
        Validate that the required API key for a provider is set.
        
        Args:
            provider: The LLM provider name
            
        Raises:
            APIKeyError: If the required API key is not set
        """
        if provider.lower() in ["gpt-turbo", "openai", "gpt-4", "40"]:
            if not os.environ.get("OPENAI_API_KEY"):
                raise APIKeyError(
                    "OPENAI_API_KEY environment variable is not set. "
                    "Please set it with: export OPENAI_API_KEY=your-api-key"
                )
        elif provider.lower() == "claude":
            if not os.environ.get("ANTHROPIC_API_KEY"):
                raise APIKeyError(
                    "ANTHROPIC_API_KEY environment variable is not set. "
                    "Please set it with: export ANTHROPIC_API_KEY=your-api-key"
                )
    
    @staticmethod
    def create_llm(
        provider: str, 
        model: str, 
        temperature: float = 0.0,
        max_retries: int = 3,
        retry_delay: int = 2
    ) -> BaseChatModel:
        """
        Create an LLM instance based on provider and model.
        
        Args:
            provider: The LLM provider name
            model: The model name
            temperature: The temperature for generation
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
            
        Returns:
            An LLM instance
            
        Raises:
            LLMProviderError: If the provider is not supported
        """
        # Validate API key
        LLMFactory.validate_api_key(provider)
        
        # Create LLM instance based on provider
        provider = provider.lower()
        
        try:
            if provider in ["gpt-turbo", "openai"]:
                from langchain.chat_models import ChatOpenAI
                return ChatOpenAI(
                    model_name=model, 
                    temperature=temperature,
                    request_timeout=60,
                    max_retries=max_retries
                )
            elif provider == "claude":
                from langchain.chat_models import ChatAnthropic
                return ChatAnthropic(
                    model=model, 
                    temperature=temperature,
                    max_retries=max_retries
                )
            elif provider == "gpt-4" or provider == "40":
                from langchain.chat_models import ChatOpenAI
                return ChatOpenAI(
                    model_name=model, 
                    temperature=temperature,
                    request_timeout=90,  # Longer timeout for GPT-4
                    max_retries=max_retries
                )
            else:
                raise LLMProviderError(f"Unsupported LLM provider: {provider}")
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize {provider} with model {model}: {str(e)}")


class CachingLLM:
    """Wrapper class for LLM with caching capability."""
    
    def __init__(self, llm: BaseChatModel, cache_size: int = 100):
        """
        Initialize the caching LLM.
        
        Args:
            llm: The base LLM instance
            cache_size: Size of the LRU cache
        """
        self.llm = llm
        self.cache_size = cache_size
        
    @lru_cache(maxsize=100)
    def _cached_call(self, messages_str: str) -> str:
        """Cached call implementation using message string as key."""
        # This is a simplified caching approach
        return self.llm.predict(messages_str)
    
    async def acall(self, messages: list[BaseMessage], **kwargs) -> Any:
        """
        Async call with retries and exponential backoff.
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments
            
        Returns:
            The LLM response
        """
        max_retries = kwargs.get("max_retries", 3)
        base_delay = kwargs.get("base_delay", 2)
        
        # Try to get from cache if simple enough
        if len(messages) == 1:
            try:
                # For simple single-message cases, we can use the cache
                content = self._cached_call(messages[0].content)
                # Return a message-like object with content
                return type('obj', (object,), {'content': content})
            except Exception:
                # If caching fails, fall back to normal call
                pass
        
        # Otherwise use normal acall with retries
        for attempt in range(max_retries):
            try:
                return await self.llm.acall(messages, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"LLM call failed (attempt {attempt+1}/{max_retries}): {str(e)}. "
                        f"Retrying in {delay} seconds..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"LLM call failed after {max_retries} attempts: {str(e)}")
                    raise


def get_llm(agent_type: str = None) -> CachingLLM:
    """
    Get an LLM instance for a specific agent type.
    
    Args:
        agent_type: The type of agent (research, coding, etc.)
        
    Returns:
        A CachingLLM instance
    """
    llm_configs = settings.get("llm", {})
    
    # If an agent_type is provided and exists in the config, use it;
    # otherwise, use a default configuration.
    if agent_type and agent_type in llm_configs:
        config = llm_configs[agent_type]
    else:
        config = llm_configs.get("default", {"provider": "gpt-turbo", "model": "gpt-3.5-turbo"})
    
    provider = config.get("provider", "gpt-turbo")
    model = config.get("model", "gpt-3.5-turbo")
    temperature = config.get("temperature", 0.0)
    
    logger.info(f"Creating LLM for agent_type={agent_type}, provider={provider}, model={model}")
    
    # Create the base LLM
    llm = LLMFactory.create_llm(provider, model, temperature)
    
    # Wrap it with caching
    return CachingLLM(llm)
