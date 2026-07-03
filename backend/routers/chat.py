import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, Language
from services.claude_service import stream_chat
from services.language_service import detect_language
from services.rag_service import retrieve_context, get_rag_status

router = APIRouter()

_DEMO_SIP_HINDI = (
    "रमेश जी, ₹5,000 प्रति माह के SIP से 10 साल में लगभग ₹11.6 लाख बनेंगे। "
    "मैं आपको HDFC Flexi Cap Fund में SIP शुरू करने की सलाह दूंगी — "
    "यह moderate risk profile के लिए उपयुक्त है। "
    "क्या आप अपने retirement goal के बारे में भी जानना चाहेंगे?"
)


@router.post("/chat")
async def chat(req: ChatRequest):
    """Main streaming chat endpoint with language detection and RAG."""
    if req.message == "DEMO_MODE_SIP_HINDI":
        async def demo_stream():
            for word in _DEMO_SIP_HINDI.split(" "):
                yield word + " "
                await asyncio.sleep(0.05)
        return StreamingResponse(
            demo_stream(),
            media_type="text/plain",
            headers={"X-Detected-Language": "hi"},
        )

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


@router.get("/rag/status")
async def rag_status():
    """Get RAG pipeline status and document count."""
    return get_rag_status()
