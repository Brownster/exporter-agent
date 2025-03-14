#models/schemas.py
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class CodeArtifact(BaseModel):
    files: Dict[str, str]

class TestResult(BaseModel):
    passed: bool
    output: str

class ResearchResult(BaseModel):
    metrics: List[Dict[str, str]] = []
    existing_code: Dict[str, str] = Field(default_factory=dict)
    structure_analysis: Dict[str, Any] = Field(default_factory=dict)

class IDECommand(BaseModel):
    command: str
    args: List[str] = Field(default_factory=list)
    timeout: int = 30

class ValidatedCodeArtifact(CodeArtifact):
    validation_errors: List[str] = Field(default_factory=list)
    formatted_code: Optional[str] = None
