#agents/validation_agent.py
import os
import subprocess
from typing import Tuple
from models.schemas import ValidatedCodeArtifact, CodeArtifact, IDECommand
from config import settings

class ValidationAgent:
    def __init__(self):
        self.tools = settings["go_tools"]
        # Build IDECommand instances from settings
        self.ide_commands = {
            key: IDECommand(command=tool["command"], args=tool.get("args", []), timeout=30)
            for key, tool in self.tools.items()
        }

    def run_ide_command(self, tool: str, file_path: str) -> Tuple[bool, str]:
        cmd_config = self.ide_commands.get(tool)
        if not cmd_config:
            return False, f"Unknown tool: {tool}"
        try:
            cmd = [cmd_config.command] + cmd_config.args + [file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=cmd_config.timeout)
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)

    def validate_code(self, artifact: CodeArtifact) -> ValidatedCodeArtifact:
        validated = ValidatedCodeArtifact(**artifact.dict())
        temp_files = []
        try:
            for filename, code in artifact.files.items():
                temp_files.append(filename)
                with open(filename, "w") as f:
                    f.write(code)
                # Run Go formatting
                success, fmt_output = self.run_ide_command("format", filename)
                if not success:
                    validated.validation_errors.append(f"Format errors in {filename}:\n{fmt_output}")
                # Run vet
                success, vet_output = self.run_ide_command("vet", filename)
                if not success:
                    validated.validation_errors.append(f"Vet errors in {filename}:\n{vet_output}")
                # Run lint
                success, lint_output = self.run_ide_command("lint", filename)
                if lint_output:
                    validated.validation_errors.append(f"Lint warnings in {filename}:\n{lint_output}")
                # Run security scan
                success, sec_output = self.run_ide_command("security", filename)
                if not success:
                    validated.validation_errors.append(f"Security issues in {filename}:\n{sec_output}")
                with open(filename, "r") as f:
                    validated.formatted_code = f.read()
            return validated
        finally:
            # Remove temporary files only if there were validation errors.
            if validated.validation_errors:
                for fname in temp_files:
                    if os.path.exists(fname):
                        os.remove(fname)
