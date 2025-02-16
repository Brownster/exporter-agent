import json
from langchain.schema import HumanMessage
from models.schemas import CodeArtifact, ResearchResult
from config import prompts
from agents.llm_provider import get_llm

class CodingAgent:
    def __init__(self):
        self.llm = get_llm()
        
    async def generate_exporter(self, research: ResearchResult) -> CodeArtifact:
        prompt = prompts["coding_prompts"]["main"].format(
            metrics=json.dumps(research.metrics)
        )
        messages = [HumanMessage(content=prompt)]
        
        response = await self.llm.acall(messages)
        return CodeArtifact(files={"exporter.go": response.content})

    async def generate_tests(self) -> CodeArtifact:
        response = await self.llm.acall([HumanMessage(content=prompts["coding_prompts"]["tests"])])
        return CodeArtifact(files={"exporter_test.go": response.content})
