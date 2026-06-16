from backend.utils.mistral_client import ask_mistral
from backend.utils.prompts import FAQ_PROMPT

def faq_agent(query):
    return ask_mistral(
        FAQ_PROMPT + "\n\nCustomer Question:\n" + query
    )