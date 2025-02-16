import asyncio
import re
import subprocess
from typing import List, Dict, Any
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

class Orchestrator:
    def __init__(self, target: str):
        self.target = target
        self.max_retries = settings["app_settings"]["max_retries"]
        self.research_agent = ResearchAgent()
        self.coding_agent = CodingAgent()
        self.validation_agent = ValidationAgent()
        self.testing_agent = EnhancedTestingAgent()
        self.dashboard_agent = DashboardAgent()
        self.alert_agent = AlertAgent()

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
        # Research phase with retries
        research = await self._retry_research()
        # Generate exporter code
        exporter_artifact = await self.coding_agent.generate_exporter(research)
        # Initialize Go module
        module_name = settings["app_settings"]["module_name"]
        subprocess.run(["go", "mod", "init", module_name], capture_output=True, text=True)
        subprocess.run(["go", "mod", "tidy"], capture_output=True, text=True)
        # Validate code
        validated = self.validation_agent.validate_code(exporter_artifact)
        retries = 0
        while validated.validation_errors and retries < self.max_retries:
            validated = await self.fix_code_errors(validated, research)
            retries += 1
        if validated.validation_errors:
            raise ValueError("Failed to generate valid code after multiple attempts")
        # Generate test files and add them
        test_artifact = await self.coding_agent.generate_tests()
        exporter_artifact.files.update(test_artifact.files)
        self._write_files_safely(exporter_artifact)
        # Run tests
        test_result = self.testing_agent.run_tests()
        if not test_result.passed:
            await self._diagnose_test_failure(test_result)
        
        # Generate dashboard design based on final metrics
        dashboard_design = await self.dashboard_agent.generate_dashboard_design(research.metrics)
        # Save dashboard design to /dashboards/dashboard.txt
        with open("dashboards/dashboard.txt", "w") as f:
            f.write(dashboard_design)
        print("Dashboard design saved to /dashboards/dashboard.txt")
        
        # Generate alert suggestions based on final metrics
        alert_suggestions = await self.alert_agent.generate_alert_suggestions(research.metrics)
        # Save alert suggestions to /alerts/alerts.txt
        with open("alerts/alerts.txt", "w") as f:
            f.write(alert_suggestions)
        print("Alert suggestions saved to /alerts/alerts.txt")
        
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
                with open(filename, "w") as f:
                    f.write(content)
                print(f"Successfully wrote {filename}")
            except IOError as e:
                print(f"Failed to write {filename}: {str(e)}")
                raise

    async def _retry_research(self, max_retries=3) -> ResearchResult:
        for attempt in range(max_retries):
            research = await self.research_agent.research_system(self.target)
            try:
                self.validate_metrics(research.metrics)
                return research
            except ValueError as e:
                if attempt == max_retries - 1:
                    raise
                print(f"Research validation failed, retrying... ({attempt+1}/{max_retries})")
                await asyncio.sleep(1)

    async def _diagnose_test_failure(self, test_result: TestResult):
        diagnosis_prompt = (
            f"Tests failed with output: {test_result.output}\n"
            "Analyze the test failures and suggest fixes for the following code:\n"
            f"{self.testing_agent.get_current_code()}"
        )
        llm = get_llm(agent_type="testing")
        messages = [
            SystemMessage(content=prompts["system_messages"]["default"]),
            HumanMessage(content=diagnosis_prompt)
        ]
        diagnosis_response = await llm.acall(messages)
        print(f"Test Failure Diagnosis:\n{diagnosis_response.content}")
