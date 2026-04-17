import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="RAG Movie Chatbot API")


class ChatRequest(BaseModel):
    message: str
    model: str = "llama-3.1-8b-instant"


@app.get("/")
def health():
    return {
        "ok": True,
        "message": "rag-movie-chatbot is live",
        "endpoints": {
            "health": "GET /",
            "chat_help": "GET /chat",
            "chat": "POST /chat"
        }
    }


@app.get("/chat")
def chat_get_help():
    return {
        "ok": True,
        "hint": "Use POST /chat with JSON body: {\"message\":\"Suggest 5 thriller movies\"}"
    }


@app.post("/chat")
def chat(req: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY in environment variables")

    user_message = (req.message or "").strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model=req.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful movie recommendation assistant. "
                        "Give concise, high-quality recommendations with brief reasons."
                    )
                },
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
        )

        reply = completion.choices[0].message.content or ""
        return {
            "ok": True,
            "reply": reply,
            "model": req.model
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")