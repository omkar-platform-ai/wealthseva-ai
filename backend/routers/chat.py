from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, Language
from services.claude_service import stream_chat
from services.language_service import detect_language
from services.rag_service import retrieve_context

router = APIRouter()


@router.post("/chat")
async def chat(req: ChatRequest):
    """Main streaming chat endpoint with language detection and RAG."""
    # Detect language from input, fall back to user preference
    detected_lang = detect_language(req.message, fallback=req.language)
    effective_lang = detected_lang if detected_lang != Language.EN else req.language

    # Retrieve IDBI context via RAG
    context = await retrieve_context(req.message, effective_lang)

    async def generate():
        async for chunk in stream_chat(req.message, req.history, effective_lang, context):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain",
                              headers={"X-Detected-Language": effective_lang.value})
