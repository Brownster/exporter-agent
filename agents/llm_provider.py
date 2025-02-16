# agents/llm_provider.py
from config import settings

def get_llm(agent_type: str = None):
    llm_configs = settings.get("llm", {})
    
    # If an agent_type is provided and exists in the config, use it;
    # otherwise, use a default configuration.
    if agent_type and agent_type in llm_configs:
        config = llm_configs[agent_type]
    else:
        config = llm_configs.get("default", {"provider": "gpt-turbo", "model": "gpt-3.5-turbo"})
    
    provider = config.get("provider", "gpt-turbo").lower()
    model = config.get("model", "gpt-3.5-turbo")
    
    if provider == "gpt-turbo":
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(model_name=model, temperature=0)
    elif provider == "claude":
        from langchain.chat_models import ChatAnthropic
        return ChatAnthropic(model=model, temperature=0)
    elif provider == "40":
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(model_name=model, temperature=0)
    else:
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(model_name=model, temperature=0)
