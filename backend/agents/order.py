from backend.utils.mistral_client import ask_mistral
from backend.utils.prompts import ORDER_PROMPT

def order_agent(query):
    return ask_mistral(
        ORDER_PROMPT + "\n\nCustomer Question:\n" + query
    )