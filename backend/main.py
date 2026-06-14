from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.agents.router import route_query
from backend.database.db import (
    init_db,
    save_chat,
    get_chats
)

app = FastAPI(
    title="Multi-Agent Customer Support System",
    version="1.0.0"
)

init_db()


class ChatRequest(BaseModel):
    query: str


@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Multi-Agent Customer Support API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat")
def chat(data: ChatRequest):

    try:
        response = route_query(data.query)

        save_chat(
            data.query,
            response
        )

        return {
            "success": True,
            "query": data.query,
            "response": response
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/history")
def history():

    try:
        chats = get_chats()

        return {
            "success": True,
            "total_chats": len(chats),
            "history": chats
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)