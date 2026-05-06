import json
from fastapi import FastAPI, Request

app = FastAPI()

VERIFY_TOKEN = "my_super_duper_looper_secret_token_123"  # you choose this

@app.get("/")
def home():
    
    return {"welcome": "welcome to the WhatsApp webhook server!"}

@app.get("/webhook/whatsapp")
def verify_webhook(
    hub_mode: str | None = None,
    hub_challenge: str | None = None,
    hub_verify_token: str | None = None,
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge) if hub_challenge is not None else 0
    return {"error": "Verification failed"}

@app.post("/webhook/whatsapp")
async def receive_message(request: Request):
    try:
        raw_body = await request.body()
        print("Raw body:", raw_body)
        
        data = json.loads(raw_body)
        print("Incoming webhook:", data)
        return {"status": "ok"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}