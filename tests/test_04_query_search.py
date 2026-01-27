"""
Query and Search API Tests

Tests for query operations including semantic search, RAG summarization,
filtering, and pagination.
"""

import pytest
import time


@pytest.fixture(scope="class")
def seeded_corpus(client, test_corpus_key):
    """Seed the test corpus with documents for search testing."""
    documents = [
        {
            "id": "search_doc_1",
            "text": "Artificial intelligence and machine learning are transforming industries. "
                    "Deep learning neural networks can process vast amounts of data to find patterns "
                    "that humans might miss. AI is being used in healthcare, finance, and transportation.",
            "metadata": {"category": "technology", "topic": "ai"},
        },
        {
            "id": "search_doc_2",
            "text": "Vector databases enable semantic search capabilities. Unlike traditional keyword search, "
                    "vector search understands the meaning and context of queries. This allows for "
                    "more accurate and relevant search results.",
            "metadata": {"category": "technology", "topic": "databases"},
        },
        {
            "id": "search_doc_3",
            "text": "Climate change is affecting weather patterns around the world. Scientists are studying "
                    "the impact of greenhouse gases on global temperatures. Renewable energy sources "
                    "like solar and wind power are becoming more important.",
            "metadata": {"category": "science", "topic": "climate"},
        },
        {
            "id": "search_doc_4",
            "text": "The Python programming language is popular for data science and machine learning. "
                    "Libraries like NumPy, Pandas, and TensorFlow make it easy to work with data "
                    "and build AI models. Python is known for its readable syntax.",
            "metadata": {"category": "technology", "topic": "programming"},
        },
        {
            "id": "search_doc_5",
            "text": "Space exploration has led to many technological innovations. NASA and SpaceX are "
                    "working on missions to Mars. Satellite technology enables global communications "
                    "and weather forecasting.",
            "metadata": {"category": "science", "topic": "space"},
        },
    ]

    # Index all documents
    for doc in documents:
        response = client.index_document(
            corpus_key=test_corpus_key,
            document_id=doc["id"],
            text=doc["text"],
            metadata=doc["metadata"],
        )
        if not response.success:
            pytest.skip(f"Could not seed corpus: {response.data}")

    # Allow time for indexing to complete
    time.sleep(2)

    yield test_corpus_key

    # Cleanup
    for doc in documents:
        client.delete_document(test_corpus_key, doc["id"])


class TestQuerySearch:
    """Test suite for query and search operations."""

    def test_basic_query(self, client, seeded_corpus):
        """Test basic semantic search query."""
        response = client.query(
            corpus_key=seeded_corpus,
            query_text="What is artificial intelligence?",
            limit=5,
        )

        assert response.success, (
            f"Query failed: {response.status_code} - {response.data}"
        )

        # Should return search results
        assert "search_results" in response.data or "results" in response.data, (
            "Expected search results in response"
        )

    def test_query_returns_relevant_results(self, client, seeded_corpus):
        """Test that query returns semantically relevant results."""
        response = client.query(
            corpus_key=seeded_corpus,
            query_text="machine learning and neural networks",
            limit=3,
        )

        assert response.success, f"Query failed: {response.status_code}"

        # Results should be returned
        results = response.data.get("search_results", response.data.get("results", []))
        assert len(results) > 0, "Expected at least one search result"

    def test_query_with_limit(self, client, seeded_corpus):
        """Test query with result limit."""
        response = client.query(
            corpus_key=seeded_corpus,
            query_text="technology",
            limit=2,
        )

        assert response.success, f"Query failed: {response.status_code}"

        results = response.data.get("search_results", response.data.get("results", []))
        assert len(results) <= 2, f"Expected at most 2 results, got {len(results)}"

    def test_query_with_offset(self, client, seeded_corpus):
        """Test query with pagination offset."""
        # First query without offset
        response1 = client.query(
            corpus_key=seeded_corpus,
            query_text="science and technology",
            limit=2,
            offset=0,
        )

        # Second query with offset
        response2 = client.query(
            corpus_key=seeded_corpus,
            query_text="science and technology",
            limit=2,
            offset=2,
        )

        assert response1.success and response2.success, "Queries failed"

        # Results should be different (pagination working)
        results1 = response1.data.get("search_results", response1.data.get("results", []))
        results2 = response2.data.get("search_results", response2.data.get("results", []))

        if len(results1) > 0 and len(results2) > 0:
            # First result of each page should be different
            id1 = results1[0].get("document_id", results1[0].get("id"))
            id2 = results2[0].get("document_id", results2[0].get("id"))
            assert id1 != id2, "Offset pagination not working correctly"

    def test_query_with_summary(self, client, seeded_corpus):
        """Test query with RAG summarization."""
        response = client.query_with_summary(
            corpus_key=seeded_corpus,
            query_text="How is AI being used today?",
            max_results=3,
        )

        assert response.success, (
            f"Query with summary failed: {response.status_code} - {response.data}"
        )

        # Should contain generated summary
        assert "summary" in response.data or "generation" in response.data, (
            "Expected summary/generation in response"
        )

    def test_query_empty_results(self, client, seeded_corpus):
        """Test query that returns no relevant results."""
        response = client.query(
            corpus_key=seeded_corpus,
            query_text="quantum teleportation through wormholes in the 15th century",
            limit=5,
        )

        assert response.success, f"Query failed: {response.status_code}"
        # Query should succeed even with no/few relevant results

    def test_query_special_characters(self, client, seeded_corpus):
        """Test query with special characters."""
        response = client.query(
            corpus_key=seeded_corpus,
            query_text="What's the purpose of AI & machine-learning?",
            limit=3,
        )

        assert response.success, (
            f"Query with special characters failed: {response.status_code}"
        )

    def test_query_unicode(self, client, seeded_corpus):
        """Test query with unicode characters."""
        response = client.query(
            corpus_key=seeded_corpus,
            query_text="intelig\u00eancia artificial e aprendizado de m\u00e1quina",
            limit=3,
        )

        assert response.success, (
            f"Query with unicode failed: {response.status_code}"
        )

    def test_query_long_text(self, client, seeded_corpus):
        """Test query with longer query text."""
        long_query = (
            "I am interested in learning about how artificial intelligence and "
            "machine learning technologies are being applied in various industries "
            "such as healthcare and finance. Can you provide information about "
            "the latest developments in deep learning and neural networks?"
        )

        response = client.query(
            corpus_key=seeded_corpus,
            query_text=long_query,
            limit=5,
        )

        assert response.success, (
            f"Long query failed: {response.status_code}"
        )

    def test_query_response_time(self, client, seeded_corpus):
        """Test that queries complete in acceptable time."""
        response = client.query(
            corpus_key=seeded_corpus,
            query_text="artificial intelligence",
            limit=5,
        )

        assert response.success, f"Query failed: {response.status_code}"
        assert response.elapsed_ms < 5000, (
            f"Query took too long: {response.elapsed_ms:.1f}ms"
        )

    def test_summary_response_time(self, client, seeded_corpus):
        """Test that RAG summarization completes in acceptable time."""
        response = client.query_with_summary(
            corpus_key=seeded_corpus,
            query_text="What are the main topics covered?",
            max_results=3,
        )

        assert response.success, f"Summary query failed: {response.status_code}"
        # RAG takes longer due to LLM generation
        assert response.elapsed_ms < 30000, (
            f"Summary took too long: {response.elapsed_ms:.1f}ms"
        )

    def test_query_nonexistent_corpus(self, client):
        """Test querying a non-existent corpus."""
        response = client.query(
            corpus_key="nonexistent_corpus_xyz123",
            query_text="test query",
            limit=5,
        )

        assert not response.success, "Query to non-existent corpus should fail"
        assert response.status_code in [400, 404], (
            f"Expected 400 or 404, got {response.status_code}"
        )


class TestChat:
    """Test suite for chat/conversation operations.

    Note: Chat requires a configured rephraser on the instance.
    Tests will skip gracefully if rephraser is not available.
    """

    def test_create_chat(self, client, seeded_corpus):
        """Test starting a new chat conversation."""
        response = client.create_chat(
            corpus_key=seeded_corpus,
            query_text="Tell me about AI",
        )

        # Skip if chat rephraser not configured on this instance
        if not response.success and "rephraser" in str(response.data).lower():
            pytest.skip("Chat rephraser not configured on this instance")

        assert response.success, (
            f"Create chat failed: {response.status_code} - {response.data}"
        )

        # Should return chat ID
        chat_id = response.data.get("chat_id")
        if chat_id:
            # Cleanup
            client.delete_chat(chat_id)

    def test_list_chats(self, client):
        """Test listing chat conversations."""
        response = client.list_chats(limit=10)

        assert response.success, (
            f"List chats failed: {response.status_code} - {response.data}"
        )

    def test_chat_turn(self, client, seeded_corpus):
        """Test adding turns to a chat conversation."""
        # Create chat
        create_response = client.create_chat(
            corpus_key=seeded_corpus,
            query_text="What is machine learning?",
        )

        if not create_response.success:
            pytest.skip("Could not create chat for turn test")

        chat_id = create_response.data.get("chat_id")
        if not chat_id:
            pytest.skip("No chat_id in response")

        # Add follow-up turn
        turn_response = client.add_chat_turn(
            chat_id=chat_id,
            query_text="Can you give me an example?",
            corpus_key=seeded_corpus,
        )

        assert turn_response.success, (
            f"Add chat turn failed: {turn_response.status_code} - {turn_response.data}"
        )

        # Cleanup
        client.delete_chat(chat_id)

    def test_delete_chat(self, client, seeded_corpus):
        """Test deleting a chat conversation."""
        # Create chat
        create_response = client.create_chat(
            corpus_key=seeded_corpus,
            query_text="Test chat for deletion",
        )

        if not create_response.success:
            pytest.skip("Could not create chat for deletion test")

        chat_id = create_response.data.get("chat_id")
        if not chat_id:
            pytest.skip("No chat_id in response")

        # Delete chat
        delete_response = client.delete_chat(chat_id)

        assert delete_response.success, (
            f"Delete chat failed: {delete_response.status_code} - {delete_response.data}"
        )
