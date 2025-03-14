"""Mock LLM for testing."""
from typing import List, Dict, Any, Optional

from langchain.schema import BaseMessage, HumanMessage, SystemMessage, AIMessage


class MockLLMResponse:
    """Mock response from LLM calls."""
    
    def __init__(self, content: str):
        """Initialize with content."""
        self.content = content


class MockLLM:
    """
    Mock LLM for testing that returns predefined responses based on input patterns.
    """
    
    def __init__(self, responses: Optional[Dict[str, str]] = None):
        """
        Initialize with optional predefined responses.
        
        Args:
            responses: Dictionary mapping prompt substrings to responses
        """
        self.responses = responses or {}
        self.default_response = '{"metrics": [{"name": "test_metric", "description": "Test metric", "type": "gauge", "sample_value": "10"}]}'
        self.call_history = []
    
    def add_response(self, prompt_substring: str, response: str) -> None:
        """
        Add a response for a specific prompt substring.
        
        Args:
            prompt_substring: Substring to match in prompts
            response: Response to return when matched
        """
        self.responses[prompt_substring] = response
    
    def set_default_response(self, response: str) -> None:
        """
        Set the default response when no match is found.
        
        Args:
            response: Default response
        """
        self.default_response = response
    
    def _find_matching_response(self, prompt: str) -> str:
        """
        Find a matching response for the prompt.
        
        Args:
            prompt: Prompt to match
            
        Returns:
            Matching response or default response
        """
        for substring, response in self.responses.items():
            if substring in prompt:
                return response
        return self.default_response
    
    def predict(self, prompt: str) -> str:
        """
        Predict response for a prompt.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Response string
        """
        self.call_history.append({"prompt": prompt, "type": "predict"})
        return self._find_matching_response(prompt)
    
    async def acall(self, messages: List[BaseMessage], **kwargs) -> MockLLMResponse:
        """
        Async call with messages.
        
        Args:
            messages: List of messages
            **kwargs: Additional arguments
            
        Returns:
            MockLLMResponse with content
        """
        # Extract content from messages
        prompt = " ".join([msg.content for msg in messages])
        self.call_history.append({"messages": messages, "kwargs": kwargs, "type": "acall"})
        return MockLLMResponse(self._find_matching_response(prompt))
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """
        Get history of calls made to this mock.
        
        Returns:
            List of call details
        """
        return self.call_history
    
    def clear_history(self) -> None:
        """Clear call history."""
        self.call_history = []


# Predefined mock responses for common scenarios
MOCK_RESEARCH_RESPONSE = """
{
  "metrics": [
    {
      "name": "aws_connect_queue_length",
      "description": "Number of calls waiting in queue",
      "sample_value": "10",
      "type": "gauge",
      "api_command": "GetCurrentMetricData with Queues filter"
    },
    {
      "name": "aws_connect_agent_online",
      "description": "Number of agents currently online",
      "sample_value": "25",
      "type": "gauge",
      "api_command": "GetCurrentMetricData with Agents filter"
    }
  ]
}
"""

MOCK_CODE_RESPONSE = """
package main

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"net/http"
)

var queueLength = prometheus.NewGauge(prometheus.GaugeOpts{
	Name: "aws_connect_queue_length",
	Help: "Number of calls waiting in queue",
})

func main() {
	prometheus.MustRegister(queueLength)
	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":8080", nil)
}
"""

MOCK_TEST_RESPONSE = """
package main

import (
	"testing"
	"net/http/httptest"
)

func TestMetricsEndpoint(t *testing.T) {
	server := httptest.NewServer(promhttp.Handler())
	defer server.Close()
	
	resp, err := http.Get(server.URL)
	if err != nil {
		t.Fatal(err)
	}
	
	if resp.StatusCode != 200 {
		t.Errorf("Expected status code 200, got %d", resp.StatusCode)
	}
}
"""

MOCK_DASHBOARD_RESPONSE = """
# AWS Connect Exporter Dashboard

This dashboard provides a comprehensive view of your AWS Connect metrics.

## Panels:
1. Queue Length - Line chart showing queue length over time
2. Agents Online - Gauge showing number of active agents
"""

MOCK_ALERT_RESPONSE = """
# AWS Connect Alert Rules

## Queue Length Alert
- Condition: aws_connect_queue_length > 20 for 5m
- Severity: warning
- Message: High call queue detected

## Agent Availability Alert
- Condition: aws_connect_agent_online < 5 for 5m
- Severity: critical
- Message: Critical agent shortage
"""