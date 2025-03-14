import json
import re
from typing import Dict, List, Any
from langchain.schema import HumanMessage
from models.schemas import CodeArtifact, ResearchResult
from config import prompts, settings
from agents.llm_provider import get_llm
from logging_utils import get_logger

logger = get_logger()

class CodingAgent:
    def __init__(self):
        self.llm = get_llm(agent_type="coding")
        self.target = settings["app_settings"]["module_name"]
        
    async def generate_exporter(self, research: ResearchResult) -> CodeArtifact:
        """
        Generate exporter code based on research results.
        
        Args:
            research: Research results with metrics
            
        Returns:
            Code artifact with generated files
        """
        # Check if we're extending an existing exporter
        if research.existing_code:
            return await self._extend_exporter(research)
        else:
            return await self._create_new_exporter(research)
    
    async def _create_new_exporter(self, research: ResearchResult) -> CodeArtifact:
        """
        Create a new exporter from scratch.
        
        Args:
            research: Research results with metrics
            
        Returns:
            Code artifact with generated files
        """
        prompt = prompts["coding_prompts"]["main"].format(
            target=self.target,
            metrics=json.dumps(research.metrics)
        )
        messages = [HumanMessage(content=prompt)]
        
        response = await self.llm.acall(messages)
        
        # Parse the response to extract multiple files
        files = self._parse_coding_response(response.content)
        
        # Fallback if parsing fails
        if not files:
            logger.warning("Failed to parse multiple files from response, using single file fallback")
            files = {"exporter.go": response.content}
            
        return CodeArtifact(files=files)
    
    async def _extend_exporter(self, research: ResearchResult) -> CodeArtifact:
        """
        Extend an existing exporter with new metrics.
        
        Args:
            research: Research results with existing code and metrics
            
        Returns:
            Code artifact with modified files
        """
        # Filter metrics to only include new ones
        new_metrics = [m for m in research.metrics if m.get("status") == "new"]
        if not new_metrics:
            logger.warning("No new metrics to add, returning existing code")
            return CodeArtifact(files=research.existing_code)
        
        # Create a summary of the code structure
        structure_summary = self._create_structure_summary(
            research.existing_code, research.structure_analysis
        )
        
        # Format the extension prompt
        prompt = prompts["coding_prompts"]["extension"].format(
            structure_summary=structure_summary,
            new_metrics=json.dumps(new_metrics)
        )
        
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.acall(messages)
        
        # Parse the response to extract modified files
        modified_files = self._parse_coding_response(response.content)
        
        # Merge existing and modified files
        result_files = dict(research.existing_code)
        for file_path, content in modified_files.items():
            result_files[file_path] = content
            logger.info(f"Modified file: {file_path}")
            
        return CodeArtifact(files=result_files)

    async def generate_tests(self) -> CodeArtifact:
        """
        Generate test files for the exporter.
        
        Returns:
            Code artifact with test files
        """
        response = await self.llm.acall([HumanMessage(content=prompts["tests"])])
        
        # Parse the response to extract multiple test files
        files = self._parse_coding_response(response.content)
        
        # Fallback if parsing fails
        if not files:
            logger.warning("Failed to parse multiple test files from response, using single file fallback")
            files = {"exporter_test.go": response.content}
            
        return CodeArtifact(files=files)
    
    def _parse_coding_response(self, content: str) -> Dict[str, str]:
        """
        Parse coding response to extract multiple files.
        
        Args:
            content: LLM response content
            
        Returns:
            Dictionary mapping file paths to file contents
        """
        files = {}
        
        # Try to extract files using Markdown code blocks
        file_blocks = re.findall(r'```(?:go)?\s*(?:filepath=([\w\/\.]+))?\s*\n(.*?)```', 
                                content, re.DOTALL)
        
        if file_blocks:
            for file_path, file_content in file_blocks:
                # If no file path specified, try to guess from content
                if not file_path:
                    if "func main(" in file_content:
                        file_path = f"cmd/{self.target}/main.go"
                    elif "TestMetrics" in file_content:
                        file_path = "exporter_test.go"
                    else:
                        file_path = "exporter.go"
                        
                files[file_path] = file_content.strip()
                logger.debug(f"Extracted file from response: {file_path}")
        
        # Alternative pattern for file blocks without Markdown
        if not files:
            alternative_blocks = re.findall(r'// ([\w\/\.]+)\n(.*?)(?=// [\w\/\.]+|\Z)', 
                                        content, re.DOTALL)
            for file_path, file_content in alternative_blocks:
                files[file_path] = file_content.strip()
                logger.debug(f"Extracted file using alternative pattern: {file_path}")
        
        return files
    
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
        
        # Add information about the code structure
        if structure_analysis.get("main_file"):
            main_file = structure_analysis["main_file"]
            summary.append(f"Main file: {main_file}")
            
        if structure_analysis.get("collector_files"):
            collector_files = structure_analysis["collector_files"]
            summary.append(f"Collector files: {', '.join(collector_files)}")
            
        if structure_analysis.get("package_name"):
            pkg_name = structure_analysis["package_name"]
            summary.append(f"Package name: {pkg_name}")
            
        # Add all file contents
        summary.append("\nFile contents:")
        for file_path, content in existing_code.items():
            summary.append(f"\n--- {file_path} ---\n{content}")
            
        return "\n".join(summary)
