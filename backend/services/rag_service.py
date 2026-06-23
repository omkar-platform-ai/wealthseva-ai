"""
RAG service using Pinecone — retrieves relevant IDBI dataset context
for grounded, factual Claude responses.
"""
import os
from pinecone import Pinecone
from langchain_anthropic import AnthropicEmbeddings
from models.schemas import Language

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
INDEX_NAME = os.getenv("PINECONE_INDEX", "wealthseva-idbi")

# Separate Pinecone namespace per language
NAMESPACE_MAP = {
    Language.EN: "idbi-data-en",
    Language.HI: "idbi-data-hi",
    Language.MR: "idbi-data-mr",
    Language.TA: "idbi-data-ta",
    Language.BN: "idbi-data-bn",
}


def get_index():
    return pc.Index(INDEX_NAME)


async def retrieve_context(query: str, language: Language, top_k: int = 3) -> str:
    """Retrieve relevant IDBI dataset chunks for the given query."""
    try:
        index = get_index()
        namespace = NAMESPACE_MAP.get(language, "idbi-data-en")

        # Use Anthropic embeddings to embed the query
        embeddings = AnthropicEmbeddings(model="voyage-3")
        query_vector = embeddings.embed_query(query)

        results = index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )

        if not results.matches:
            return ""

        context_parts = [
            match.metadata.get("text", "") for match in results.matches
        ]
        return "\n\n".join(context_parts)
    except Exception:
        # RAG failure is non-fatal — Claude will respond without context
        return ""
