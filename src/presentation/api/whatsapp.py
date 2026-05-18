"""WhatsApp webhook API routes.

These handlers are intentionally thin: they own only HTTP concerns
(parsing requests, returning responses, status codes). All business
logic is delegated to the application service layer.
"""
from fastapi import APIRouter, HTTPException, Query, Request

from config import WebhookConfig
from ..dependencies import (
    ConversationContextServiceDep,
    ConversationServiceDep,
    LeadExtractionServiceDep,
    WhatsAppServiceDep,
)
from ..schemas.whatsapp import (
    ContextMessage,
    ConversationResponse,
    LeadExtractionResponse,
    WebhookPayload,
)

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


@router.get(
    "/conversations",
    response_model=list[ConversationResponse],
)
async def list_conversations(
    service: ConversationServiceDep,
    limit: int = Query(default=20, ge=1, le=20),
):
    conversations = await service.list_conversations(limit)
    return [
        ConversationResponse(
            id=conversation.id,
            contact_id=conversation.contact_id,
            phone_number_id=conversation.phone_number_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        )
        for conversation in conversations
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(
    conversation_id: int,
    service: ConversationServiceDep,
):
    conversation = await service.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        id=conversation.id,
        contact_id=conversation.contact_id,
        phone_number_id=conversation.phone_number_id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


@router.get(
    "/conversations/{conversation_id}/context",
    response_model=list[ContextMessage],
)
async def get_conversation_context(
    conversation_id: int,
    service: ConversationContextServiceDep,
    limit: int = 10,
):
    return await service.get_recent_context(conversation_id, limit)


@router.get(
    "/conversations/{conversation_id}/lead-extraction",
    response_model=LeadExtractionResponse,
)
async def extract_lead(
    conversation_id: int,
    service: LeadExtractionServiceDep,
    limit: int = 10,
):
    """Fetch the last *limit* messages for a conversation, build the transcript,
    and return AI-extracted lead intent and summary."""
    result = await service.extract_from_conversation(conversation_id, limit)
    return LeadExtractionResponse(
        intent=result.intent,
        summary=result.summary,
        location=result.location,
        products=result.products,
        customer_needs=result.customer_needs,
        budget_hint=result.budget_hint,
        lead_temperature=result.lead_temperature,
    )
