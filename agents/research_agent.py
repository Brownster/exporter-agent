#agents/research_agent.py
import json
from typing import Dict, Any, List
from langchain.schema import HumanMessage, SystemMessage
from models.schemas import ResearchResult
from config import prompts
from agents.llm_provider import get_llm
from logging_utils import get_logger

logger = get_logger()

class ResearchAgent:
    def __init__(self):
        self.llm = get_llm(agent_type="research")
        self.system_message = SystemMessage(content=prompts["system_messages"]["default"])
        
    async def research_system(self, target: str) -> ResearchResult:
        """
        Research appropriate metrics for a new exporter.
        
        Args:
            target: Name of the target exporter
            
        Returns:
            Research results with discovered metrics
        """
        prompt = prompts["research_prompts"]["main"].format(target=target)
        messages = [self.system_message, HumanMessage(content=prompt)]
        
        response = await self.llm.acall(messages)
        try:
            data = json.loads(response.content)
            return ResearchResult(metrics=data.get("metrics", []))
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from research agent")
            # Fallback if JSON parsing fails.
            return ResearchResult(metrics=[{
                "name": "aws_connect_queue_length",
                "description": "Number of calls waiting in queue",
                "sample_value": "10",
                "type": "gauge"
            }])
            
    async def research_with_existing_code(
        self, target: str, existing_code: Dict[str, str], structure_analysis: Dict[str, Any]
    ) -> ResearchResult:
        """
        Research metrics from existing code and suggest new ones.
        
        Args:
            target: Name of the target exporter
            existing_code: Dictionary mapping file paths to file contents
            structure_analysis: Analysis of the exporter structure
            
        Returns:
            Research results with existing and new suggested metrics
        """
        # Create a summary of the code structure for the prompt
        structure_summary = self._create_structure_summary(existing_code, structure_analysis)
        
        # Format the prompt with the code structure
        prompt = prompts["research_prompts"]["extension"].format(
            target=target,
            structure_summary=structure_summary
        )
        
        # Send the message to the LLM
        messages = [self.system_message, HumanMessage(content=prompt)]
        response = await self.llm.acall(messages)
        
        try:
            # Parse the JSON response
            data = json.loads(response.content)
            metrics = data.get("metrics", [])
            
            # Count existing and new metrics
            existing_count = len([m for m in metrics if m.get("status") == "existing"])
            new_count = len([m for m in metrics if m.get("status") == "new"])
            logger.info(f"Found {existing_count} existing metrics and {new_count} new suggested metrics")
            
            # Create the research result
            return ResearchResult(
                metrics=metrics,
                existing_code=existing_code,
                structure_analysis=structure_analysis
            )
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from research agent")
            # Create a simple fallback
            return ResearchResult(
                metrics=[{
                    "name": "example_metric",
                    "description": "Example metric",
                    "sample_value": "10",
                    "type": "gauge",
                    "status": "new"
                }],
                existing_code=existing_code,
                structure_analysis=structure_analysis
            )
    
    def _create_structure_summary(
        self, existing_code: Dict[str, str], structure_analysis: Dict[str, Any]
    ) -> str:
        """
        Create a summary of the code structure for the prompt.
        
        Args:
            existing_code: Dictionary mapping file paths to file contents
            structure_analysis: Analysis of the exporter structure
            
        Returns:
            A string summarizing the code structure
        """
        summary = []
        
        # Add information about the main file
        if structure_analysis.get("main_file"):
            main_file = structure_analysis["main_file"]
            summary.append(f"Main file: {main_file}")
            
        # Add information about collector files
        if structure_analysis.get("collector_files"):
            collector_files = structure_analysis["collector_files"]
            summary.append(f"Collector files: {', '.join(collector_files)}")
            
        # Add information about package name
        if structure_analysis.get("package_name"):
            pkg_name = structure_analysis["package_name"]
            summary.append(f"Package name: {pkg_name}")
            
        # Add information about imports
        if structure_analysis.get("imports"):
            imports = structure_analysis["imports"]
            summary.append(f"Key imports: {', '.join(list(imports)[:10])}")
            
        # Add file content summaries (limited to save context)
        summary.append("\nFile content summaries:")
        for file_path, content in existing_code.items():
            # Limit the amount of content shown for each file
            content_preview = content.split("\n")[:30]
            content_summary = "\n".join(content_preview)
            if len(content_preview) < len(content.split("\n")):
                content_summary += "\n... (truncated)"
                
            summary.append(f"\n--- {file_path} ---\n{content_summary}")
            
        return "\n".join(summary)
