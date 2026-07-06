"""
RAG service using Pinecone + Amazon Bedrock Titan embeddings — retrieves
relevant IDBI dataset context for grounded, factual Claude responses.
"""
import os
import re
import json
import time
import asyncio
import hashlib
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

# Curated local knowledge base used when Pinecone is not configured.
# Lives inside backend/ so it ships with the Docker image (build context is backend/).
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_LOCAL_KB_PATH = os.path.join(_DATA_DIR, "knowledge_base.json")

# Precomputed Titan-v2 embeddings for the local KB (scripts/embed_knowledge_base.py).
# Optional: when the file is absent or stale, retrieval degrades to keyword matching.
# Generated offline so the server never bursts 106 Bedrock calls at startup.
_KB_EMBEDDINGS_PATH = os.path.join(_DATA_DIR, "knowledge_base_embeddings.json")

# Vernacular finance-term expansion map (HI/MR/TA/BN token -> English KB tokens),
# so Indic-script queries retrieve from the English-language knowledge base even
# without embeddings.
_VERNACULAR_TERMS_PATH = os.path.join(_DATA_DIR, "vernacular_terms.json")

_EMBED_MODEL_ID = os.getenv("EMBED_MODEL_ID", "amazon.titan-embed-text-v2:0")
# Cosine floor below which a chunk is considered irrelevant. Cross-lingual
# matches score lower than same-language ones, so this is deliberately lenient.
_SEMANTIC_FLOOR = 0.25
# After an embed failure (e.g. Bedrock throttling), skip the semantic path for
# this long instead of burning one doomed Bedrock call per chat message.
_EMBED_COOLDOWN_SECONDS = 300


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


# Words too common to signal relevance in a finance query
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "in", "on", "of", "for", "to",
    "and", "or", "what", "which", "how", "my", "i", "me", "you", "should",
    "do", "does", "can", "with", "about", "tell", "please", "want", "much",
}


# \w alone SPLITS Indic words: Python's re does not count combining vowel
# signs / virama (category Mn, e.g. ी ् ா  ু) as word characters, so
# "एसआईपी" would tokenize as "एसआईप". Include the full Devanagari, Bengali,
# and Tamil blocks so hi/mr/bn/ta words survive intact.
_TOKEN_RE = re.compile(r"[\wऀ-ॿঀ-৿஀-௿]+")


def _tokenize(text: str) -> set:
    """Lowercase word tokens minus stopwords; keeps Indic words whole."""
    return {w for w in _TOKEN_RE.findall(text.lower()) if w not in _STOPWORDS}


_vernacular_terms: dict | None = None


def _load_vernacular_terms() -> dict:
    """Load (once) the Indic term -> English tokens map; {} if unavailable."""
    global _vernacular_terms
    if _vernacular_terms is None:
        try:
            with open(_VERNACULAR_TERMS_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            _vernacular_terms = {k: v for k, v in raw.items() if isinstance(v, list)}
        except Exception:
            _vernacular_terms = {}
    return _vernacular_terms


def _expand_query_tokens(tokens: set) -> set:
    """Add English equivalents for any Indic finance terms in the query."""
    terms = _load_vernacular_terms()
    expanded = set(tokens)
    for tok in tokens:
        hit = terms.get(tok)
        if hit:
            expanded.update(hit)
            continue
        # Indic case suffixes (साठी / में / -ির / -த்திற்கு …) attach to the
        # stem, so fall back to prefix matching. Only for keys of 4+ chars —
        # short keys would false-match unrelated words.
        for key, values in terms.items():
            if len(key) >= 4 and tok.startswith(key):
                expanded.update(values)
    return expanded


def _keyword_matching(query: str, chunks: list, top_k: int = 3) -> str:
    """Score chunks by token overlap; curated keywords count double."""
    query_words = _expand_query_tokens(_tokenize(query))
    if not query_words:
        return ""

    scored_chunks = []
    for chunk in chunks:
        text = chunk.get("text", "")
        text_words = _tokenize(text)
        keyword_words = {k.lower() for k in chunk.get("keywords", [])}
        score = len(query_words & text_words) + 2 * len(query_words & keyword_words)
        if score > 0:
            scored_chunks.append((score, text))

    # Sort by score (descending) and take top_k
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [text for score, text in scored_chunks[:top_k]]

    return "\n\n".join(top_chunks) if top_chunks else ""


async def retrieve_context(query: str, language: Language, top_k: int = 3) -> str:
    """Retrieve relevant IDBI dataset chunks for the given query."""
    try:
        index = _get_index()
        if index is None:
            # No API key configured, use local knowledge base fallback
            return await _local_retrieve(query, top_k)

        namespace = NAMESPACE_MAP.get(language, "idbi-data-en")

        # Use Amazon Bedrock Titan embeddings for vector search
        from langchain_aws.embeddings import BedrockEmbeddings

        # Create Bedrock embeddings client with region
        embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=_BEDROCK_REGION,
        )

        # Generate query vector — embed_query is a blocking boto3 call,
        # so run it off the event loop with its own timeout
        query_vector = await asyncio.wait_for(
            asyncio.to_thread(embeddings.embed_query, query),
            timeout=3.0,
        )

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
        # Embedding or Pinecone query timed out — log warning and use local fallback
        print(f"WARNING: RAG query timed out for query: {query[:50]}...")
        return await _local_retrieve(query, top_k)
    except Exception as e:
        # RAG failure is non-fatal — log warning and use local fallback
        print(f"WARNING: RAG query failed: {e}")
        return await _local_retrieve(query, top_k)


async def _local_retrieve(query: str, top_k: int = 3) -> str:
    """Local RAG: semantic (precomputed embeddings) first, keyword fallback."""
    try:
        if not os.path.exists(_LOCAL_KB_PATH):
            # Knowledge base missing, return empty context (non-fatal)
            return ""

        with open(_LOCAL_KB_PATH, 'r') as f:
            chunks = json.load(f)

        semantic = await _semantic_retrieve(query, chunks, top_k)
        if semantic:
            return semantic
        return _keyword_matching(query, chunks, top_k)
    except Exception:
        # Local retrieval failed — return empty context (non-fatal)
        return ""


# ---- Local semantic retrieval (precomputed KB embeddings + query embed) ----

# None = not loaded yet; False = determined unavailable; tuple = ready
_semantic_index = None
_semantic_cooldown_until = 0.0
_bedrock_embed_client = None


def _reset_semantic_cache():
    """Test hook: forget the cached index / cooldown / client."""
    global _semantic_index, _semantic_cooldown_until, _bedrock_embed_client
    _semantic_index = None
    _semantic_cooldown_until = 0.0
    _bedrock_embed_client = None


def _kb_file_sha256() -> str:
    with open(_LOCAL_KB_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _load_semantic_index(chunks: list):
    """Load the precomputed KB embedding matrix once; None when unavailable.

    A missing embeddings file is the normal state until the Bedrock embeddings
    quota is granted and scripts/embed_knowledge_base.py has been run — only a
    STALE file (KB edited after embedding) warrants a warning.
    """
    global _semantic_index
    if _semantic_index is not None:
        return _semantic_index or None
    try:
        if not os.path.exists(_KB_EMBEDDINGS_PATH):
            _semantic_index = False
            return None
        with open(_KB_EMBEDDINGS_PATH, "r") as f:
            payload = json.load(f)
        if payload.get("kb_sha256") != _kb_file_sha256():
            print("WARNING: knowledge_base_embeddings.json is stale — rerun "
                  "scripts/embed_knowledge_base.py; using keyword retrieval")
            _semantic_index = False
            return None
        embeddings = payload["embeddings"]
        pairs = [(c["id"], c["text"]) for c in chunks if c.get("id") in embeddings]
        if not pairs:
            _semantic_index = False
            return None
        import numpy as np
        matrix = np.asarray([embeddings[cid] for cid, _ in pairs], dtype=np.float32)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        _semantic_index = (matrix, [text for _, text in pairs])
    except Exception as e:
        print(f"WARNING: failed to load KB embeddings: {e}")
        _semantic_index = False
        return None
    return _semantic_index


def _embed_query_sync(text: str) -> list:
    """Embed one query with Titan v2. Fail fast: one attempt, tight timeouts,
    so a throttled/unavailable Bedrock degrades to keyword matching quickly."""
    global _bedrock_embed_client
    if _bedrock_embed_client is None:
        import boto3
        from botocore.config import Config
        _bedrock_embed_client = boto3.client(
            "bedrock-runtime",
            region_name=_BEDROCK_REGION,
            config=Config(retries={"max_attempts": 1}, connect_timeout=2, read_timeout=3),
        )
    body = json.dumps({"inputText": text[:2000], "dimensions": 1024, "normalize": True})
    response = _bedrock_embed_client.invoke_model(modelId=_EMBED_MODEL_ID, body=body)
    return json.loads(response["body"].read())["embedding"]


async def _semantic_retrieve(query: str, chunks: list, top_k: int = 3) -> str:
    """Cosine top-k over the precomputed KB embeddings; "" when unavailable
    (caller falls back to keyword matching)."""
    global _semantic_cooldown_until
    index = _load_semantic_index(chunks)
    if index is None or time.time() < _semantic_cooldown_until:
        return ""
    matrix, texts = index

    try:
        vector = await asyncio.wait_for(asyncio.to_thread(_embed_query_sync, query), timeout=4.0)
    except Exception as e:
        _semantic_cooldown_until = time.time() + _EMBED_COOLDOWN_SECONDS
        print(f"WARNING: query embedding failed ({e}); keyword retrieval for "
              f"{_EMBED_COOLDOWN_SECONDS}s")
        return ""

    import numpy as np
    q = np.asarray(vector, dtype=np.float32)
    norm = float(np.linalg.norm(q))
    if not norm:
        return ""
    scores = matrix @ (q / norm)
    order = np.argsort(scores)[::-1][:top_k]
    picked = [texts[i] for i in order if scores[i] >= _SEMANTIC_FLOOR]
    return "\n\n".join(picked)


def get_rag_status() -> dict:
    """Get RAG pipeline status for health checks."""
    pinecone_connected = _get_index() is not None
    doc_count = 0
    local_mode = "keyword"

    if pinecone_connected:
        try:
            index = _get_index()
            # Try to get stats from Pinecone
            stats = index.describe_index_stats()
            doc_count = stats.get('total_vector_count', 0)
        except Exception:
            pass
    elif os.path.exists(_LOCAL_KB_PATH):
        # Count local knowledge base documents
        try:
            with open(_LOCAL_KB_PATH, 'r') as f:
                chunks = json.load(f)
            doc_count = len(chunks)
            if _load_semantic_index(chunks) is not None:
                local_mode = "semantic"
        except Exception:
            pass

    return {
        "pinecone_connected": pinecone_connected,
        "doc_count": doc_count,
        "local_mode": local_mode,
    }
