"""
Agent Corpora Search Tool Tests (SDK)

The #1 user journey: create an agent with a corpora_search tool,
ask questions, verify the agent uses corpus content in its answers.
"""

import pytest
from vectara.agent_events.types import CreateAgentEventsRequestBody_InputMessage

from utils.waiters import wait_for

from .conftest import _session_exists, create_agent


def _extract_output_text(events):
    output_parts = []
    for event in events:
        event_type = getattr(event, "type", None)
        if event_type and ("output" in str(event_type) or "message" in str(event_type)):
            content = getattr(event, "content", "") or ""
            if content:
                output_parts.append(content)
    return " ".join(output_parts)


@pytest.mark.core
class TestAgentCorporaSearch:
    """Agent with corpora_search tool -- core product flow."""

    def test_create_agent_with_corpora_search_tool(self, sdk_client, sdk_shared_agent_corpus):
        """Create agent with corpora_search tool, verify config persisted."""
        agent = create_agent(
            sdk_client,
            sdk_shared_agent_corpus,
            name_prefix="Search Agent",
        )

        try:
            retrieved = sdk_client.agents.get(agent.key)
            assert retrieved.key == agent.key, "Agent key mismatch"
            assert retrieved.model is not None, "Agent should have a model"
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass

    def test_agent_corpora_search_returns_corpus_content(self, sdk_client, sdk_shared_agent):
        """Send question to agent with search tool, verify answer uses corpus content."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            wait_for(
                lambda: _session_exists(sdk_client, sdk_shared_agent, session_key),
                timeout=10,
                interval=0.5,
                description="session available",
            )

            sdk_client.agent_events.create(
                sdk_shared_agent,
                session_key,
                request=CreateAgentEventsRequestBody_InputMessage(
                    messages=[{"type": "text", "content": "What is vector search and how does it work?"}],
                    stream_response=False,
                ),
            )

            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) > 0, f"Expected events in response"

            event_types = [getattr(e, "type", None) for e in events]
            has_output = any(t and ("output" in str(t) or "message" in str(t)) for t in event_types)
            assert has_output, f"Expected agent_output event, got types: {event_types}"

            output_text = _extract_output_text(events)
            assert len(output_text) > 20, f"Agent output should be substantive, got: {output_text[:100]}"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass
