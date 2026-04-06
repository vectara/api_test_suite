"""
Agent-specific fixtures.

Provides a module-scoped corpus with agent-focused documents and a reusable
shared agent for execution and session tests.  CRUD tests create their own
agents per-test since they mutate agent state.
"""

import logging
import uuid

import pytest

from utils.waiters import wait_for

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def shared_agent_corpus(client):
    """Module-scoped corpus with agent-focused docs."""
    corpus_key = f"agent_corpus_{uuid.uuid4().hex}"

    response = client.create_corpus(
        name=f"Agent Test Corpus {uuid.uuid4().hex[:8]}",
        key=corpus_key,
        description="Shared agent test corpus",
    )
    if not response.success:
        pytest.skip(f"Could not create agent corpus: {response.data}")

    actual_key = response.data.get("key", corpus_key)

    docs = [
        {
            "id": f"agent_doc_{uuid.uuid4().hex[:8]}",
            "text": "Vectara is a trusted AI platform for enterprise search and RAG applications.",
            "metadata": {"topic": "overview"},
        },
        {
            "id": f"agent_doc_{uuid.uuid4().hex[:8]}",
            "text": "To get started with Vectara, create an account and obtain an API key with QueryService and IndexService permissions.",
            "metadata": {"topic": "getting_started"},
        },
        {
            "id": f"agent_doc_{uuid.uuid4().hex[:8]}",
            "text": "Vectara agents provide conversational AI experiences maintaining context across multiple turns.",
            "metadata": {"topic": "agents"},
        },
    ]

    doc_ids = []
    for doc in docs:
        resp = client.index_document(
            corpus_key=actual_key,
            document_id=doc["id"],
            text=doc["text"],
            metadata=doc["metadata"],
        )
        if resp.success:
            doc_ids.append(doc["id"])

    wait_for(
        lambda: client.list_documents(actual_key, limit=1).data.get("documents", []),
        timeout=15,
        interval=1,
        description="agent corpus documents to be indexed",
    )

    yield actual_key

    for doc_id in doc_ids:
        try:
            client.delete_document(actual_key, doc_id)
        except Exception:
            pass
    try:
        client.delete_corpus(actual_key)
    except Exception:
        pass


@pytest.fixture(scope="module")
def shared_agent(client, shared_agent_corpus):
    """Module-scoped agent for execution and session tests.

    Do NOT use for tests that mutate agent properties (update, delete, identity).
    Those tests should create their own agent.
    """
    agent_key = f"test_agent_{uuid.uuid4().hex[:8]}"

    response = client.create_agent(
        name=f"Shared Test Agent {uuid.uuid4().hex[:8]}",
        corpus_keys=[shared_agent_corpus],
        description="Shared agent for execution testing",
    )

    # Fallback to minimal agent
    if not response.success:
        response = client.create_agent(
            name=f"Shared Test Agent {uuid.uuid4().hex[:8]}",
            description="Shared agent for execution testing",
        )

    if not response.success:
        pytest.skip(f"Could not create shared agent: {response.data}")

    agent_id = response.data.get("id") or response.data.get("agent_id") or response.data.get("key")
    if not agent_id:
        pytest.skip("No agent key in response")

    yield agent_id

    try:
        client.delete_agent(agent_id)
    except Exception:
        pass


@pytest.fixture
def agent_with_session(client, shared_agent):
    """Create a session on shared_agent, send a message, yield (agent_key, session_key, events)."""
    session_resp = client.create_agent_session(shared_agent)
    if not session_resp.success:
        pytest.skip(f"Could not create agent session: {session_resp.data}")

    session_key = session_resp.data.get("key")

    # Send a message to generate events
    client.execute_agent(agent_id=shared_agent, query_text="Setup message", session_id=session_key)

    # List events
    events_resp = client.list_session_events(shared_agent, session_key)
    events = events_resp.data.get("events", []) if events_resp.success else []

    yield shared_agent, session_key, events

    try:
        client.delete_agent_session(shared_agent, session_key)
    except Exception:
        pass
