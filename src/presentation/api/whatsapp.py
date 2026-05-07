"""WhatsApp webhook API routes.

These handlers are intentionally thin: they own only HTTP concerns
(parsing requests, returning responses, status codes). All business
logic is delegated to the application service layer.
"""
from fastapi import APIRouter, HTTPException, Request

from config import WebhookConfig
from ..dependencies import WhatsAppServiceDep
from ..schemas.whatsapp import WebhookPayload

router = APIRouter()


@router.get("/")
def home():
    return {"welcome": "welcome to the WhatsApp webhook server!"}


@router.get("/webhook/whatsapp")
def verify_webhook(
    hub_mode: str | None = None,
    hub_challenge: str | None = None,
    hub_verify_token: str | None = None,
):
    if hub_mode == "subscribe" and hub_verify_token == WebhookConfig.VERIFY_TOKEN:
        return int(hub_challenge) if hub_challenge is not None else 0
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.post("/webhook/whatsapp")
async def receive_message(
    request: Request,
    service: WhatsAppServiceDep,
):
    """Receive a WhatsApp Cloud API webhook event.

    FastAPI validates the payload against `WebhookPayload` automatically
    and returns 422 if the body does not conform to the schema.
    """
    # Get raw request body before parsing
    raw_body = await request.body()
    print(f"[WEBHOOK] RAW REQUEST BODY: {raw_body.decode('utf-8')}", flush=True)
    
    try:
        # Parse raw body to WebhookPayload
        payload = WebhookPayload.model_validate_json(raw_body)
        print(f"[WEBHOOK] Parsed payload model: {payload.model_dump()}", flush=True)
        print(f"[WEBHOOK] Processing webhook with {len(payload.entry)} entries", flush=True)
        await service.process_incoming_webhook(payload)
        print(f"[WEBHOOK] Successfully processed webhook", flush=True)
        return {"status": "ok"}
    except Exception as e:
        print(f"[WEBHOOK] Error processing webhook: {e}", flush=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal server error")
