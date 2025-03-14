"""Orchestration module for the exporter-agent."""
import asyncio
import re
import subprocess
import os
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

from models.schemas import ResearchResult, ValidatedCodeArtifact, TestResult, CodeArtifact
from config import prompts, settings
from agents.research_agent import ResearchAgent
from agents.coding_agent import CodingAgent
from agents.validation_agent import ValidationAgent
from agents.testing_agent import EnhancedTestingAgent
from agents.dashboard_agent import DashboardAgent
from agents.alert_agent import AlertAgent
from agents.llm_provider import get_llm
from langchain.schema import HumanMessage, SystemMessage
from exceptions import ResearchError, CodeGenerationError, ValidationError, TestingError
from logging_utils import get_logger

# Get logger
logger = get_logger()

class Orchestrator:
    """Main orchestrator for the exporter-agent pipeline."""
    
    def __init__(self, target: str, mode: str = "create", exporter_path: str = None):
        """
        Initialize the orchestrator.
        
        Args:
            target: Target exporter name
            mode: Operation mode ("create" or "extend")
            exporter_path: Path to existing exporter code for extension mode
        """
        self.target = target
        self.mode = mode
        self.exporter_path = exporter_path
        self.max_retries = settings["app_settings"]["max_retries"]
        
        # Initialize agents
        logger.info(f"Initializing agents for target: {target} in {mode} mode")
        self.research_agent = ResearchAgent()
        self.coding_agent = CodingAgent()
        self.validation_agent = ValidationAgent()
        self.testing_agent = EnhancedTestingAgent()
        self.dashboard_agent = DashboardAgent()
        self.alert_agent = AlertAgent()
        
        # Create ThreadPoolExecutor for parallel tasks
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Validate extension mode requirements
        if mode == "extend" and not exporter_path:
            logger.error("Extension mode requires an exporter path")
            raise ValueError("Extension mode requires an exporter path")

    def validate_metrics(self, metrics: List[Dict[str, str]]):
        allowed_types = {"gauge", "counter", "histogram"}
        for metric in metrics:
            name = metric.get("name", "")
            if not re.match(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$', name):
                raise ValueError(f"Invalid metric name: {name}")
            if not metric.get("description"):
                raise ValueError("All metrics must have descriptions")
            if metric.get("type") not in allowed_types:
                raise ValueError(f"Invalid metric type: {metric.get('type')}")

    async def run_agents(self) -> Dict[str, Any]:
        """
        Run all agents in the pipeline.
        
        Returns:
            Dictionary of results
            
        Raises:
            Various exceptions depending on the stage that fails
        """
        # Create necessary directories 
        for directory in ["cmd", "collectors", "connect", "dashboards", "alerts", "logs"]:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Created directory: {directory}")
        
        try:
            # Research phase depends on mode
            logger.info("Starting research phase")
            if self.mode == "extend":
                from utils.file_utils import load_existing_exporter, analyze_exporter_structure
                
                # Load existing code
                logger.info(f"Loading existing exporter code from {self.exporter_path}")
                existing_code = load_existing_exporter(self.exporter_path)
                
                if not existing_code:
                    logger.error("No valid Go files found in the specified path")
                    raise ValueError("No valid Go files found in the specified path")
                
                # Analyze code structure
                logger.info("Analyzing exporter structure")
                structure_analysis = analyze_exporter_structure(existing_code)
                
                # Research with existing code
                research = await self._research_with_existing_code(existing_code, structure_analysis)
                
                logger.info(f"Research complete: discovered {len(research.metrics)} metrics " +
                            f"(new and existing) from {len(existing_code)} files")
            else:
                # Standard research for new exporter
                research = await self._retry_research()
                logger.info(f"Research complete: discovered {len(research.metrics)} metrics")
            
            # Generate exporter code
            logger.info("Generating exporter code")
            exporter_artifact = await self.coding_agent.generate_exporter(research)
            logger.info(f"Code generation complete: {len(exporter_artifact.files)} files")
            
            # Initialize Go module and install dependencies in parallel
            logger.info("Initializing Go module and installing dependencies")
            await self._setup_go_environment()
            
            # Validate code
            logger.info("Validating generated code")
            validated = self.validation_agent.validate_code(exporter_artifact)
            
            # Fix code if needed
            retries = 0
            while validated.validation_errors and retries < self.max_retries:
                logger.warning(f"Validation failed with {len(validated.validation_errors)} errors (attempt {retries+1}/{self.max_retries})")
                validated = await self.fix_code_errors(validated, research)
                retries += 1
                
            if validated.validation_errors:
                logger.error(f"Failed to generate valid code after {self.max_retries} attempts")
                raise ValidationError(f"Failed to generate valid code after {self.max_retries} attempts")
                
            # Generate test files
            logger.info("Generating test files")
            test_artifact = await self.coding_agent.generate_tests()
            exporter_artifact.files.update(test_artifact.files)
            
            # Write all files
            logger.info("Writing files to disk")
            self._write_files_safely(exporter_artifact)
            
            # Run tests
            logger.info("Running tests")
            test_result = self.testing_agent.run_tests()
            if not test_result.passed:
                logger.warning(f"Tests failed: {test_result.output[:100]}...")
                await self._diagnose_test_failure(test_result)
            else:
                logger.info("All tests passed")
            
            # Generate dashboard and alerts in parallel
            logger.info("Generating dashboard and alert configurations")
            dashboard_future = self.dashboard_agent.generate_dashboard_design(research.metrics)
            alert_future = self.alert_agent.generate_alert_suggestions(research.metrics)
            
            dashboard_design, alert_suggestions = await asyncio.gather(dashboard_future, alert_future)
            
            # Save dashboard design
            with open("dashboards/dashboard.txt", "w") as f:
                f.write(dashboard_design)
            logger.info("Dashboard design saved to dashboards/dashboard.txt")
            
            # Save alert suggestions
            with open("alerts/alerts.txt", "w") as f:
                f.write(alert_suggestions)
            logger.info("Alert suggestions saved to alerts/alerts.txt")
            
            return {
                "research": research,
                "code": validated,
                "test_result": test_result,
                "dashboard": dashboard_design,
                "alerts": alert_suggestions
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise
    
    async def _setup_go_environment(self) -> None:
        """Set up Go environment with modules and dependencies."""
        try:
            # Initialize module
            module_name = settings["app_settings"]["module_name"]
            result = subprocess.run(
                ["go", "mod", "init", module_name], 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                logger.warning(f"Go module init failed: {result.stderr}")
            
            # Define required dependencies
            go_deps = [
                "github.com/prometheus/client_golang/prometheus",
                "github.com/prometheus/client_golang/prometheus/promhttp",
                "github.com/aws/aws-sdk-go/aws",
                "github.com/aws/aws-sdk-go/aws/session",
                "github.com/aws/aws-sdk-go/service/connect",
                "gopkg.in/alecthomas/kingpin.v2"
            ]
            
            # Install dependencies in parallel using asyncio
            async def install_dep(dep):
                proc = await asyncio.create_subprocess_exec(
                    "go", "get", dep,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                return dep, proc.returncode, stdout, stderr
            
            # Create tasks for all dependencies
            tasks = [install_dep(dep) for dep in go_deps]
            results = await asyncio.gather(*tasks)
            
            # Log results
            for dep, code, stdout, stderr in results:
                if code != 0:
                    logger.warning(f"Failed to install {dep}: {stderr.decode()}")
                else:
                    logger.debug(f"Installed {dep}")
            
            # Tidy modules
            tidy_result = subprocess.run(
                ["go", "mod", "tidy"], 
                capture_output=True, 
                text=True
            )
            
            if tidy_result.returncode != 0:
                logger.warning(f"Go mod tidy failed: {tidy_result.stderr}")
                
        except Exception as e:
            logger.error(f"Failed to set up Go environment: {str(e)}")
            raise CodeGenerationError(f"Failed to set up Go environment: {str(e)}")
        
        return {
            "research": research,
            "code": validated,
            "test_result": test_result,
            "dashboard": dashboard_design,
            "alerts": alert_suggestions
        }

    async def fix_code_errors(self, validated: ValidatedCodeArtifact, research: ResearchResult) -> ValidatedCodeArtifact:
        fix_prompt = prompts["validation_messages"]["fix_prompt"].format(
            errors=validated.validation_errors,
            code=validated.formatted_code
        )
        # Use the LLM configured for coding fixes
        llm = get_llm(agent_type="coding")
        messages = [
            SystemMessage(content=prompts["system_messages"]["default"]),
            HumanMessage(content=fix_prompt)
        ]
        response = await llm.acall(messages)
        fixed_code = response.content
        new_artifact = CodeArtifact(files={"exporter.go": fixed_code})
        return self.validation_agent.validate_code(new_artifact)

    def _write_files_safely(self, artifact: CodeArtifact):
        for filename, content in artifact.files.items():
            try:
                # Create directories if they don't exist
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, "w") as f:
                    f.write(content)
                print(f"Successfully wrote {filename}")
            except IOError as e:
                print(f"Failed to write {filename}: {str(e)}")
                raise

    async def _retry_research(self, max_retries=3) -> ResearchResult:
        """
        Perform the research phase with retries for validation errors.
        
        Args:
            max_retries: Maximum number of research attempts
            
        Returns:
            Research results
        """
        for attempt in range(max_retries):
            research = await self.research_agent.research_system(self.target)
            try:
                self.validate_metrics(research.metrics)
                return research
            except ValueError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Research validation failed, retrying... ({attempt+1}/{max_retries}): {str(e)}")
                await asyncio.sleep(1)
                
    async def _research_with_existing_code(
        self, existing_code: Dict[str, str], structure_analysis: Dict[str, Any]
    ) -> ResearchResult:
        """
        Perform research on existing exporter code to identify metrics.
        
        Args:
            existing_code: Dictionary mapping file paths to file contents
            structure_analysis: Analysis of the exporter structure
            
        Returns:
            Research results with existing metrics and suggested new metrics
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Call the agent with existing code
                research = await self.research_agent.research_with_existing_code(
                    self.target, existing_code, structure_analysis
                )
                
                # Validate the metrics
                self.validate_metrics(research.metrics)
                return research
            except ValueError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to extract valid metrics from existing code: {str(e)}")
                    raise
                logger.warning(f"Existing code research failed, retrying... ({attempt+1}/{max_retries}): {str(e)}")
                await asyncio.sleep(1)

    async def _diagnose_test_failure(self, test_result: TestResult):
        diagnosis_prompt = (
            f"Tests failed with output: {test_result.output}\n"
            "Analyze the test failures and suggest fixes for the following code:\n"
            f"{self.testing_agent.get_current_code()}"
        )
        # Use the LLM configured for testing diagnosis
        llm = get_llm(agent_type="testing")
        messages = [
            SystemMessage(content=prompts["system_messages"]["default"]),
            HumanMessage(content=diagnosis_prompt)
        ]
        diagnosis_response = await llm.acall(messages)
        print(f"Test Failure Diagnosis:\n{diagnosis_response.content}")
