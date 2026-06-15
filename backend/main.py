from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
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

# Set up static directory paths
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()



class ChatRequest(BaseModel):
    query: str





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
@app.get("/", response_class=HTMLResponse)
def serve_home():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<html><body><h1>Backend running. Frontend index.html not found yet.</h1></body></html>"