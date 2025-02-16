# agents/llm_provider.py
from config import settings

def get_llm():
    llm_config = settings.get("llm", {})
    provider = llm_config.get("provider", "gpt-turbo").lower()
    model = llm_config.get("model", "gpt-3.5-turbo")
    
    if provider == "gpt-turbo":
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(model_name=model, temperature=0)
    elif provider == "claude":
        # Example: using Anthropic's model via langchain (if supported)
        from langchain.chat_models import ChatAnthropic
        return ChatAnthropic(model=model, temperature=0)
    elif provider == "40":
        # For example, if you want to use GPT-4 via ChatOpenAI:
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(model_name=model, temperature=0)
    else:
        # Fallback to ChatOpenAI by default.
        from langchain.chat_models import ChatOpenAI
        return ChatOpenAI(model_name=model, temperature=0)
