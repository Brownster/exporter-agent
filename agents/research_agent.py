#agents/research_agent.py
import json
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from models.schemas import ResearchResult
from config import prompts

class ResearchAgent:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0)
        self.system_message = SystemMessage(content=prompts["system_messages"]["default"])
        
    async def research_system(self, target: str) -> ResearchResult:
        prompt = prompts["research_prompts"]["main"].format(target=target)
        messages = [self.system_message, HumanMessage(content=prompt)]
        
        response = await self.llm.acall(messages)
        try:
            data = json.loads(response.content)
            return ResearchResult(metrics=data.get("metrics", []))
        except json.JSONDecodeError:
            # Fallback values if JSON parsing fails.
            return ResearchResult(metrics=[{
                "name": "aws_connect_queue_length",
                "description": "Number of calls waiting in queue",
                "sample_value": "10",
                "type": "gauge"
            }])
