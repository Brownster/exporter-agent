import json
from langchain.schema import HumanMessage, SystemMessage
from config import prompts
from agents.llm_provider import get_llm

class AlertAgent:
    def __init__(self):
        self.llm = get_llm(agent_type="alert")
        self.system_message = SystemMessage(content=prompts["system_messages"]["default"])
    
    async def generate_alert_suggestions(self, metrics: list) -> str:
        prompt = prompts["alert_prompts"]["main"].format(metrics=json.dumps(metrics, indent=2))
        messages = [self.system_message, HumanMessage(content=prompt)]
        response = await self.llm.acall(messages)
        return response.content
