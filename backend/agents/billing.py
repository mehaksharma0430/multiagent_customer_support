from backend.utils.mistral_client import ask_mistral
from backend.utils.prompts import BILLING_PROMPT

def billing_agent(query):
    return ask_mistral(
        BILLING_PROMPT + "\n\nCustomer Question:\n" + query
    )