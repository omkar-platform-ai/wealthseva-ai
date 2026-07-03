"""
RAG service using Pinecone + Amazon Bedrock Titan embeddings — retrieves
relevant IDBI dataset context for grounded, factual Claude responses.
"""
import os
import json
import asyncio
from models.schemas import Language

# Lazy initialization to avoid blocking tests when API keys are not set
_PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
_INDEX_NAME = os.getenv("PINECONE_INDEX", "wealthseva-idbi")
_BEDROCK_REGION = os.getenv("BEDROCK_REGION", "ap-south-1")

# Separate Pinecone namespace per language
NAMESPACE_MAP = {
    Language.EN: "idbi-data-en",
    Language.HI: "idbi-data-hi",
    Language.MR: "idbi-data-mr",
    Language.TA: "idbi-data-ta",
    Language.BN: "idbi-data-bn",
}

# Path to mock index for fallback when Pinecone is not configured
# backend/services/rag_service.py -> go up two levels to reach project root
_MOCK_INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data/mock_index.json")


def _get_index():
    """Get Pinecone index, initialized lazily."""
    if not _PINECONE_API_KEY:
        return None
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=_PINECONE_API_KEY)
        return pc.Index(_INDEX_NAME)
    except Exception:
        return None


def _keyword_matching(query: str, chunks: list, top_k: int = 3) -> str:
    """Simple keyword matching fallback for mock index."""
    query_lower = query.lower()
    # Score each chunk by keyword overlap
    scored_chunks = []
    for chunk in chunks:
        text = chunk.get("text", "").lower()
        # Count matching words
        query_words = set(query_lower.split())
        text_words = set(text.split())
        matches = len(query_words & text_words)
        if matches > 0:
            scored_chunks.append((matches, chunk["text"]))

    # Sort by match count (descending) and take top_k
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for score, chunk in scored_chunks[:top_k]]

    return "\n\n".join(top_chunks) if top_chunks else ""


async def retrieve_context(query: str, language: Language, top_k: int = 3) -> str:
    """Retrieve relevant IDBI dataset chunks for the given query."""
    try:
        index = _get_index()
        if index is None:
            # No API key configured, use mock fallback
            return await _mock_retrieve(query, top_k)

        namespace = NAMESPACE_MAP.get(language, "idbi-data-en")

        # Use Amazon Bedrock Titan embeddings for vector search
        from langchain_aws.embeddings import BedrockEmbeddings

        # Create Bedrock embeddings client with region
        embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=_BEDROCK_REGION,
        )

        # Generate query vector
        query_vector = embeddings.embed_query(query)

        # Query Pinecone index with 2-second timeout
        results = await asyncio.wait_for(
            asyncio.to_thread(
                index.query,
                vector=query_vector,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
            ),
            timeout=2.0
        )

        if not results.matches:
            return ""

        # Extract text from metadata
        context_parts = [
            match.metadata.get("text", "") for match in results.matches
        ]
        return "\n\n".join(context_parts)

    except asyncio.TimeoutError:
        # Pinecone query timed out — log warning and use mock fallback
        print(f"WARNING: Pinecone query timed out for query: {query[:50]}...")
        return await _mock_retrieve(query, top_k)
    except Exception as e:
        # RAG failure is non-fatal — log warning and use mock fallback
        print(f"WARNING: RAG query failed: {e}")
        return await _mock_retrieve(query, top_k)


async def _mock_retrieve(query: str, top_k: int = 3) -> str:
    """Mock RAG using keyword matching against mock_index.json."""
    try:
        if not os.path.exists(_MOCK_INDEX_PATH):
            # Mock index missing, return empty context (non-fatal)
            return ""

        with open(_MOCK_INDEX_PATH, 'r') as f:
            chunks = json.load(f)

        return _keyword_matching(query, chunks, top_k)
    except Exception:
        # Mock retrieval failed — return empty context (non-fatal)
        return ""


def get_rag_status() -> dict:
    """Get RAG pipeline status for health checks."""
    pinecone_connected = _get_index() is not None
    doc_count = 0

    if pinecone_connected:
        try:
            index = _get_index()
            # Try to get stats from Pinecone
            stats = index.describe_index_stats()
            doc_count = stats.get('total_vector_count', 0)
        except Exception:
            pass
    elif os.path.exists(_MOCK_INDEX_PATH):
        # Count mock documents
        try:
            with open(_MOCK_INDEX_PATH, 'r') as f:
                chunks = json.load(f)
            doc_count = len(chunks)
        except Exception:
            pass

    return {
        "pinecone_connected": pinecone_connected,
        "doc_count": doc_count
    }
