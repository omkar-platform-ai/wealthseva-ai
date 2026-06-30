"""
Tests for chat endpoints with Bedrock integration.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from models.schemas import Language, ChatMessage


class TestBedrockIntegration:
    """Test Bedrock-based Claude service integration."""

    @pytest.mark.asyncio
    async def test_stream_chat_with_bedrock(self):
        """Test streaming chat with mocked Bedrock client."""
        # Mock the Bedrock client
        mock_bedrock = MagicMock()
        mock_stream = AsyncMock()
        mock_stream.text_stream.__aiter__ = AsyncMock(return_value=iter(["Hello", " world", "!"]))
        mock_stream.__aenter__ = AsyncMock(return_value=mock_stream)
        mock_stream.__aexit__ = AsyncMock()
        mock_bedrock.messages.stream.return_value = mock_stream

        with patch('services.claude_service.client', mock_bedrock):
            from services.claude_service import stream_chat

            response_chunks = []
            async for chunk in stream_chat(
                message="Hello",
                history=[ChatMessage(role="user", content="Hi")],
                language=Language.EN,
            ):
                response_chunks.append(chunk)

            assert response_chunks == ["Hello", " world", "!"]
            mock_bedrock.messages.stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_chat_without_credentials(self):
        """Test graceful fallback when AWS credentials are missing."""
        with patch('services.claude_service.client', None):
            from services.claude_service import stream_chat

            response_chunks = []
            async for chunk in stream_chat(
                message="Hello",
                history=[ChatMessage(role="user", content="Hi")],
                language=Language.EN,
            ):
                response_chunks.append(chunk)

            # Should return mock response, not crash
            assert len(response_chunks) == 1
            assert "unable to connect" in response_chunks[0].lower()

    @pytest.mark.asyncio
    async def test_analyze_portfolio_with_bedrock(self):
        """Test portfolio analysis with mocked Bedrock client."""
        mock_bedrock = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Buy SBI ETF and HDFC Bank")]
        mock_bedrock.messages.create = AsyncMock(return_value=mock_response)

        with patch('services.claude_service.client', mock_bedrock):
            from services.claude_service import analyze_portfolio

            result = await analyze_portfolio(
                portfolio_data={"stocks": ["SBI"]},
                language=Language.EN,
            )

            assert "SBI" in result
            assert "HDFC" in result
            mock_bedrock.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_rag_with_bedrock_embeddings(self):
        """Test RAG context retrieval with mocked Bedrock embeddings."""
        mock_index = MagicMock()
        mock_index.query.return_value = MagicMock(
            matches=[
                MagicMock(metadata={"text": "SBI offers 8% returns"}),
                MagicMock(metadata={"text": "HDFC is stable"}),
            ]
        )

        mock_embeddings = MagicMock()
        mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]

        with patch('services.rag_service._get_index', return_value=mock_index):
            with patch('langchain_aws.embeddings.BedrockEmbeddings', return_value=mock_embeddings):
                from services.rag_service import retrieve_context

                context = await retrieve_context(
                    query="Best stocks?",
                    language=Language.EN,
                )

                assert "SBI" in context
                assert "HDFC" in context
                mock_index.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_rag_graceful_failure(self):
        """Test RAG returns empty string on any error."""
        with patch('services.rag_service._get_index', side_effect=Exception("Pinecone error")):
            from services.rag_service import retrieve_context

            context = await retrieve_context(
                query="Best stocks?",
                language=Language.EN,
            )

            # Should return empty string, not crash
            assert context == ""
