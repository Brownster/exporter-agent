#agents/testing_agent.py
import subprocess
import os
import glob
from models.schemas import TestResult
from config import settings

class EnhancedTestingAgent:
    def __init__(self, **data):
        self.test_process = None
        self.test_timeout = settings["app_settings"].get("test_timeout", 60)

    def run_tests(self) -> TestResult:
        try:
            # Create test directory if it doesn't exist
            os.makedirs("collectors/testdata", exist_ok=True)
            
            # Run tests with increased timeout
            result = subprocess.run(["go", "test", "./..."], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=self.test_timeout)
            passed = result.returncode == 0
            output = result.stdout + result.stderr
            return TestResult(passed=passed, output=output)
        except Exception as e:
            return TestResult(passed=False, output=str(e))

    def get_current_code(self) -> str:
        try:
            # Collect all Go files for analysis
            go_files = glob.glob("**/*.go", recursive=True)
            code_content = []
            
            for file_path in go_files:
                with open(file_path, "r") as f:
                    content = f.read()
                code_content.append(f"// {file_path}\n{content}\n\n")
            
            return "\n".join(code_content)
        except Exception as e:
            return f"Error retrieving code: {str(e)}"
