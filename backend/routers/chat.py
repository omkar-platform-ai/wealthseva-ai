import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from models.schemas import ChatRequest, Language
from services.account_service import get_account_context
from services.claude_service import stream_chat
from services.language_service import detect_language
from services.rag_service import retrieve_context, get_rag_status

router = APIRouter()

# Keep the token stream flowing incrementally instead of being buffered whole by
# an intermediary. `X-Accel-Buffering: no` tells an nginx reverse proxy to skip
# response buffering for this response (nginx defaults to proxy_buffering on,
# which holds the full body → time-to-first-byte == total, killing progressive
# typing). `Cache-Control: no-cache` stops any layer from holding the stream to
# cache it. Harmless if no such proxy is present. See WEA-60.
_STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
}

# Compliance: recommend fund *categories*, never specific fund names (see system prompt rules)
_DEMO_SIP_HINDI = (
    "रमेश जी, ₹5,000 प्रति माह के SIP से 10 साल में लगभग ₹11.6 लाख बनेंगे। "
    "मैं आपको flexi-cap श्रेणी के diversified equity fund में SIP शुरू करने की सलाह दूंगी — "
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
            headers={**_STREAM_HEADERS, "X-Detected-Language": "hi"},
        )

    # Detect language from input, fall back to user preference
    detected_lang = detect_language(req.message, fallback=req.language)
    effective_lang = detected_lang if detected_lang != Language.EN else req.language

    # Retrieve IDBI knowledge-base context (RAG) and the customer's account
    # snapshot in parallel — both are optional and degrade to "".
    context, account_context = await asyncio.gather(
        retrieve_context(req.message, effective_lang),
        get_account_context(),
    )

    async def generate():
        async for chunk in stream_chat(req.message, req.history, effective_lang, context, account_context):
            yield chunk

    return StreamingResponse(generate(), media_type="text/plain",
                              headers={**_STREAM_HEADERS, "X-Detected-Language": effective_lang.value})


@router.get("/rag/status")
async def rag_status():
    """Get RAG pipeline status and document count."""
    return get_rag_status()
