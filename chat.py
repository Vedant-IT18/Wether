from fastapi import APIRouter
from backend.models.schemas import ChatMessageRequest, ChatMessageResponse
from backend.services.nlp_service import nlp_service

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("", response_model=ChatMessageResponse)
async def handle_chat(req: ChatMessageRequest):
    """Processes natural language weather queries and generates structured AI responses."""
    return await nlp_service.process_chat(req)
