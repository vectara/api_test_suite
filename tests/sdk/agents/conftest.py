"""
Agent-specific fixtures for SDK tests.

Session-scoped corpus and shared agent to minimize API calls.
Only tests that truly need a separate agent (delete, dedicated config)
should create their own.
"""

import logging
import uuid

import pytest
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage
from vectara.types import (
    AgentCorporaSearchQueryConfiguration,
    AgentKeyedSearchCorpus,
    AgentModel,
    AgentOutputParser_Default,
    AgentSearchCorporaParameters,
    AgentStepInstruction_Inline,
    AgentToolConfiguration_CorporaSearch,
    CoreDocumentPart,
    CreateDocumentRequest_Core,
    FirstAgentStep,
    GenerationParameters,
)

from utils.waiters import wait_for

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Builder helpers (importable by test files)
# ---------------------------------------------------------------------------


def _build_agent_tool_configs(corpus_key):
    """Build a standard corpora_search tool configuration for an agent."""
    return {
        "corpora_search": AgentToolConfiguration_CorporaSearch(
            query_configuration=AgentCorporaSearchQueryConfiguration(
                search=AgentSearchCorporaParameters(
                    corpora=[AgentKeyedSearchCorpus(corpus_key=corpus_key)],
                ),
                generation=GenerationParameters(),
            ),
        ),
    }


def _build_agent_model():
    """Build a default agent model configuration."""
    return AgentModel(name="gpt-4o")


def _build_first_step():
    """Build the required first_step for agent creation."""
    return FirstAgentStep(
        name="main",
        instructions=[
            AgentStepInstruction_Inline(
                name="system",
                template="You are a helpful assistant.",
            ),
        ],
        output_parser=AgentOutputParser_Default(),
    )


def create_agent(sdk_client, corpus_key, name_prefix="SDK Agent", description="SDK test agent"):
    """Create an agent with standard config. Use this instead of inlining creation."""
    return sdk_client.agents.create(
        name=f"{name_prefix} {uuid.uuid4().hex[:8]}",
        tool_configurations=_build_agent_tool_configs(corpus_key),
        model=_build_agent_model(),
        first_step=_build_first_step(),
        description=description,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _has_documents(sdk_client, corpus_key):
    """Return True when at least one document is present in the corpus."""
    try:
        items = list(sdk_client.documents.list(corpus_key, limit=1))
        return len(items) > 0
    except Exception:
        return False


def _session_exists(sdk_client, agent_key, session_key):
    """Return True if session is accessible."""
    try:
        sdk_client.agent_sessions.get(agent_key, session_key)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Session-scoped fixtures (created once for the entire test run)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sdk_shared_agent_corpus(sdk_client):
    """Session-scoped corpus with agent-focused docs. Created once, shared by all agent tests."""
    corpus_key = f"sdk_agent_corpus_{uuid.uuid4().hex}"

    corpus = sdk_client.corpora.create(
        name=f"SDK Agent Test Corpus {uuid.uuid4().hex[:8]}",
        key=corpus_key,
        description="Session-scoped SDK agent test corpus",
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
                    document_parts=[CoreDocumentPart(text=doc["text"], metadata=doc["metadata"])],
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


@pytest.fixture(scope="session")
def sdk_shared_agent(sdk_client, sdk_shared_agent_corpus):
    """Session-scoped agent for read-only tests (execution, sessions, events, streaming).

    Do NOT mutate this agent (update description, disable, delete) in tests.
    Tests that need to mutate should use `create_agent()` helper to make their own.
    """
    agent = create_agent(
        sdk_client,
        sdk_shared_agent_corpus,
        name_prefix="SDK Shared Agent",
        description="Session-scoped shared agent for SDK tests",
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

    wait_for(
        lambda: _session_exists(sdk_client, sdk_shared_agent, session_key),
        timeout=10,
        interval=0.5,
        description="session to be available",
    )

    sdk_client.agent_events.create(
        sdk_shared_agent,
        session_key,
        request=CreateAgentEventsRequestBody_InputMessage(
            messages=[{"type": "text", "content": "Setup message"}],
            stream_response=False,
        ),
    )

    events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))

    yield sdk_shared_agent, session_key, events

    try:
        sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
    except Exception:
        pass
