from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat import respond_to_chat

router = APIRouter(prefix="/chat", tags=["assistant"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    return respond_to_chat(payload)
