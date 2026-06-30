"""
RAG service using Pinecone + Amazon Bedrock Titan embeddings — retrieves
relevant IDBI dataset context for grounded, factual Claude responses.
"""
import os
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


def _get_index():
    """Get Pinecone index, initialized lazily."""
    if not _PINECONE_API_KEY:
        return None
    from pinecone import Pinecone
    pc = Pinecone(api_key=_PINECONE_API_KEY)
    return pc.Index(_INDEX_NAME)


async def retrieve_context(query: str, language: Language, top_k: int = 3) -> str:
    """Retrieve relevant IDBI dataset chunks for the given query."""
    try:
        index = _get_index()
        if index is None:
            # No API key configured, return empty context
            return ""

        namespace = NAMESPACE_MAP.get(language, "idbi-data-en")

        # Use Amazon Bedrock Titan embeddings for vector search
        from langchain_aws.embeddings import BedrockEmbeddings
        import boto3

        # Create Bedrock embeddings client with region
        embeddings = BedrockEmbeddings(
            model_id="amazon.titan-embed-text-v2:0",
            region_name=_BEDROCK_REGION,
        )

        # Generate query vector
        query_vector = embeddings.embed_query(query)

        # Query Pinecone index
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )

        if not results.matches:
            return ""

        # Extract text from metadata
        context_parts = [
            match.metadata.get("text", "") for match in results.matches
        ]
        return "\n\n".join(context_parts)

    except Exception:
        # RAG failure is non-fatal — Claude will respond without context
        return ""
