"""
Agent-specific fixtures.

Provides a seeded corpus with agent-focused documents and a reusable
test agent for execution and session tests.
"""

import time
import logging

import pytest

logger = logging.getLogger(__name__)


@pytest.fixture
def seeded_corpus_for_agents(client, test_corpus):
    """Seed the test corpus with documents for agent testing.

    Yields the corpus key string.
    """
    documents = [
        {
            "id": "agent_doc_1",
            "text": (
                "Vectara is a trusted AI platform for enterprise search and RAG applications. "
                "It provides semantic search, summarization, and conversational AI capabilities. "
                "Vectara supports both SaaS and on-premise deployments for enterprise customers."
            ),
            "metadata": {"category": "product", "topic": "overview"},
        },
        {
            "id": "agent_doc_2",
            "text": (
                "To get started with Vectara, you need to create an account and obtain an API key. "
                "The API key should have QueryService and IndexService permissions for full functionality. "
                "You can then use the REST API or SDKs to index documents and run queries."
            ),
            "metadata": {"category": "documentation", "topic": "getting_started"},
        },
        {
            "id": "agent_doc_3",
            "text": (
                "Vectara agents provide conversational AI experiences. Agents maintain context "
                "across multiple turns of conversation, allowing for natural follow-up questions. "
                "Each agent can be configured with specific corpora and generation settings."
            ),
            "metadata": {"category": "documentation", "topic": "agents"},
        },
    ]

    doc_ids = []

    # Index all documents
    for doc in documents:
        response = client.index_document(
            corpus_key=test_corpus,
            document_id=doc["id"],
            text=doc["text"],
            metadata=doc["metadata"],
        )
        if response.success:
            doc_ids.append(doc["id"])
        else:
            logger.warning("Failed to seed agent document %s: %s", doc["id"], response.data)

    if not doc_ids:
        pytest.skip("Could not seed any documents for agents")

    # Allow time for indexing
    time.sleep(2)

    try:
        yield test_corpus
    finally:
        for doc_id in doc_ids:
            try:
                client.delete_document(test_corpus, doc_id)
            except Exception:
                logger.warning("Failed to clean up agent document %s", doc_id, exc_info=True)


@pytest.fixture
def test_agent(client, seeded_corpus_for_agents, unique_id):
    """Create a test agent for execution tests.

    Yields the agent ID string.
    """
    response = client.create_agent(
        name=f"Execution Test Agent {unique_id}",
        corpus_keys=[seeded_corpus_for_agents],
        description="Agent for execution testing",
    )

    # Fallback to minimal agent
    if not response.success:
        response = client.create_agent(
            name=f"Execution Test Agent {unique_id}",
            description="Agent for execution testing",
        )

    if not response.success:
        pytest.skip(f"Could not create test agent: {response.data}")

    agent_id = response.data.get("id") or response.data.get("agent_id") or response.data.get("key")
    if not agent_id:
        pytest.skip("No agent_id in create response")

    try:
        yield agent_id
    finally:
        try:
            client.delete_agent(agent_id)
        except Exception:
            logger.warning("Failed to clean up test agent %s", agent_id, exc_info=True)
