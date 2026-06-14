from backend.agents.billing import billing_agent
from backend.agents.technical import technical_agent
from backend.agents.order import order_agent
from backend.agents.faq import faq_agent


def route_query(query):

    q = query.lower()

    if any(word in q for word in
           ["bill", "billing", "payment", "refund", "invoice"]):
        return billing_agent(query)

    elif any(word in q for word in
             ["error", "bug", "login", "issue", "technical"]):
        return technical_agent(query)

    elif any(word in q for word in
             ["order", "delivery", "shipping", "track"]):
        return order_agent(query)

    return faq_agent(query)