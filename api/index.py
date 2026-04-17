import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    model: str = "llama-3.1-8b-instant"  # change if you want

@app.get("/")
def health():
    return {"ok": True, "message": "rag-movie-chatbot is live"}

@app.post("/chat")
def chat(req: ChatRequest):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing GROQ_API_KEY")

    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model=req.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful movie recommendation assistant."
                },
                {
                    "role": "user",
                    "content": req.message.strip()
                }
            ],
            temperature=0.7,
        )

        answer = completion.choices[0].message.content
        return {"ok": True, "reply": answer}
    except Exception as e:
        # Surface a useful error in Vercel logs
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")