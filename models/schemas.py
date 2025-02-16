#models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class CodeArtifact(BaseModel):
    files: Dict[str, str]

class TestResult(BaseModel):
    passed: bool
    output: str

class ResearchResult(BaseModel):
    metrics: List[Dict[str, str]] = []

class IDECommand(BaseModel):
    command: str
    args: List[str] = Field(default_factory=list)
    timeout: int = 30

class ValidatedCodeArtifact(CodeArtifact):
    validation_errors: List[str] = Field(default_factory=list)
    formatted_code: Optional[str] = None
