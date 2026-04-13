"""
Agent-specific fixtures for SDK tests.

Provides a module-scoped corpus with agent-focused documents and a reusable
shared agent for execution and session tests. CRUD tests create their own
agents per-test since they mutate agent state.
"""

import logging
import uuid

import pytest

from vectara.types import (
    AgentRagConfig,
    CorporaSearchToolConfig,
    SearchCorporaParameters,
    KeyedSearchCorpus,
    GenerationParameters,
    CoreDocumentPart,
    CreateDocumentRequest_Core,
)

from utils.waiters import wait_for

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def sdk_shared_agent_corpus(sdk_client):
    """Module-scoped corpus with agent-focused docs."""
    corpus_key = f"sdk_agent_corpus_{uuid.uuid4().hex}"

    corpus = sdk_client.corpora.create(
        name=f"SDK Agent Test Corpus {uuid.uuid4().hex[:8]}",
        key=corpus_key,
        description="Shared SDK agent test corpus",
    )

    actual_key = corpus.key

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
        try:
            sdk_client.documents.create(
                actual_key,
                request=CreateDocumentRequest_Core(
                    id=doc["id"],
                    document_parts=[
                        CoreDocumentPart(
                            text=doc["text"],
                            metadata=doc["metadata"],
                        )
                    ],
                ),
            )
            doc_ids.append(doc["id"])
        except Exception as e:
            logger.warning("Failed to index agent doc %s: %s", doc["id"], e)

    wait_for(
        lambda: _has_documents(sdk_client, actual_key),
        timeout=15,
        interval=1,
        description="agent corpus documents to be indexed",
    )

    yield actual_key

    for doc_id in doc_ids:
        try:
            sdk_client.documents.delete(actual_key, doc_id)
        except Exception:
            pass
    try:
        sdk_client.corpora.delete(actual_key)
    except Exception:
        pass


def _has_documents(sdk_client, corpus_key):
    """Return True when at least one document is present in the corpus."""
    try:
        docs = sdk_client.documents.list(corpus_key, limit=1)
        items = list(docs)
        return len(items) > 0
    except Exception:
        return False


@pytest.fixture(scope="module")
def sdk_shared_agent(sdk_client, sdk_shared_agent_corpus):
    """Module-scoped agent for execution and session tests.

    Do NOT use for tests that mutate agent properties (update, delete, identity).
    Those tests should create their own agent.
    """
    try:
        agent = sdk_client.agents.create(
            name=f"SDK Shared Agent {uuid.uuid4().hex[:8]}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
            description="Shared SDK agent for execution testing",
        )
    except Exception:
        # Fallback to minimal agent
        agent = sdk_client.agents.create(
            name=f"SDK Shared Agent {uuid.uuid4().hex[:8]}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(
                    corpora=[KeyedSearchCorpus(corpus_key=sdk_shared_agent_corpus)],
                ),
                generation=GenerationParameters(),
            ),
        )

    yield agent.key

    try:
        sdk_client.agents.delete(agent.key)
    except Exception:
        pass


@pytest.fixture
def sdk_agent_with_session(sdk_client, sdk_shared_agent):
    """Create a session on sdk_shared_agent, send a message, yield (agent_key, session_key, events)."""
    session = sdk_client.agent_sessions.create(sdk_shared_agent)
    session_key = session.key

    # Send a message to generate events
    sdk_client.agent_events.create(
        agent_key=sdk_shared_agent,
        session_key=session_key,
        type="input_message",
        messages=[{"type": "text", "content": "Setup message"}],
        stream_response=False,
    )

    # List events
    events_pager = sdk_client.agent_events.list(sdk_shared_agent, session_key)
    events = list(events_pager)

    yield sdk_shared_agent, session_key, events

    try:
        sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
    except Exception:
        pass
