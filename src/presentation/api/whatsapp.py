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
    ContactInfo,
    ContextMessage,
    ConversationDetailResponse,
    ConversationListItemResponse,
    ConversationResponse,
    LeadExtractionResponse,
    MessageSummary,
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
    response_model=list[ConversationListItemResponse],
)
async def list_conversations(
    service: ConversationServiceDep,
    limit: int = Query(default=20, ge=1, le=20),
):
    summaries = await service.list_conversations_with_details(limit)
    return [
        ConversationListItemResponse(
            id=s.conversation.id,
            contact_id=s.conversation.contact_id,
            phone_number_id=s.conversation.phone_number_id,
            created_at=s.conversation.created_at,
            updated_at=s.conversation.updated_at,
            contact=ContactInfo(
                wa_id=s.contact.wa_id,
                name=s.contact.name,
            ) if s.contact else None,
            last_message=MessageSummary(
                id=s.last_message.id,
                direction=s.last_message.direction,
                message_type=s.last_message.message_type,
                text_content=s.last_message.text_content,
                message_timestamp=s.last_message.message_timestamp,
            ) if s.last_message else None,
        )
        for s in summaries
    ]


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
)
async def get_conversation(
    conversation_id: int,
    service: ConversationServiceDep,
):
    detail = await service.get_conversation_with_details(conversation_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetailResponse(
        id=detail.conversation.id,
        contact_id=detail.conversation.contact_id,
        phone_number_id=detail.conversation.phone_number_id,
        created_at=detail.conversation.created_at,
        updated_at=detail.conversation.updated_at,
        contact=ContactInfo(
            wa_id=detail.contact.wa_id,
            name=detail.contact.name,
        ) if detail.contact else None,
        messages=[
            MessageSummary(
                id=m.message.id,
                direction=m.message.direction,
                message_type=m.message.message_type,
                text_content=m.message.text_content,
                message_timestamp=m.message.message_timestamp,
                media_url=m.media_url,
                caption=m.caption,
            )
            for m in detail.messages
        ],
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
