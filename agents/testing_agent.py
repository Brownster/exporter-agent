#agents/testing_agent.py
import subprocess
from models.schemas import TestResult

class EnhancedTestingAgent:
    def __init__(self, **data):
        self.test_process = None

    def run_tests(self) -> TestResult:
        try:
            result = subprocess.run(["go", "test", "./..."], capture_output=True, text=True, timeout=60)
            passed = result.returncode == 0
            output = result.stdout + result.stderr
            return TestResult(passed=passed, output=output)
        except Exception as e:
            return TestResult(passed=False, output=str(e))

    def get_current_code(self) -> str:
        try:
            with open("exporter.go", "r") as f:
                return f.read()
        except Exception as e:
            return f"Error retrieving code: {str(e)}"
