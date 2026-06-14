from backend.utils.mistral_client import ask_mistral
from backend.utils.prompts import TECHNICAL_PROMPT

def technical_agent(query):
    return ask_mistral(
        TECHNICAL_PROMPT + "\n\nCustomer Question:\n" + query
    )