"""
Agent Session Compaction Tests (SDK)

Tests for compaction config on agents.
Note: Manual compaction and fork-with-compaction require low-level event
manipulation that may not be fully exposed via the SDK. Tests are adapted
to use available SDK methods.
"""

import uuid

import pytest

from vectara.types import (
    AgentRagConfig,
    SearchCorporaParameters,
    GenerationParameters,
)

from utils.waiters import wait_for


def _session_exists(sdk_client, agent_key, session_key):
    try:
        sdk_client.agent_sessions.get(agent_key, session_key)
        return True
    except Exception:
        return False


@pytest.mark.core
class TestCompactionConfig:
    """Agent compaction configuration tests."""

    def test_create_agent_and_verify_config(self, sdk_client, unique_id):
        """Verify agent can be created and retrieved with expected fields."""
        agent = sdk_client.agents.create(
            name=f"Compaction Agent {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(corpora=[]),
                generation=GenerationParameters(),
            ),
        )

        try:
            retrieved = sdk_client.agents.get(agent.key)
            assert retrieved.key == agent.key
            assert retrieved.name is not None
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass

    def test_update_agent_description(self, sdk_client, unique_id):
        """Verify agent description can be updated."""
        agent = sdk_client.agents.create(
            name=f"Compaction Update {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(corpora=[]),
                generation=GenerationParameters(),
            ),
        )

        try:
            sdk_client.agents.update(agent.key, description="Updated compaction config")

            retrieved = sdk_client.agents.get(agent.key)
            assert retrieved.description == "Updated compaction config"
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass


@pytest.mark.core
class TestManualCompaction:
    """Manual compaction via multi-turn sessions."""

    def test_multi_turn_session(self, sdk_client, unique_id):
        """Create agent, send multiple turns, verify events accumulate."""
        agent = sdk_client.agents.create(
            name=f"Compact Manual {unique_id}",
            type="rag",
            agent_type_config=AgentRagConfig(
                search=SearchCorporaParameters(corpora=[]),
                generation=GenerationParameters(),
            ),
        )

        try:
            session = sdk_client.agent_sessions.create(agent.key)
            session_key = session.key

            try:
                wait_for(
                    lambda: _session_exists(sdk_client, agent.key, session_key),
                    timeout=10,
                    interval=0.5,
                    description="session available",
                )

                for msg in ["Tell me about AI", "What about machine learning?", "How do neural networks work?"]:
                    sdk_client.agent_events.create(
                        agent_key=agent.key,
                        session_key=session_key,
                        type="input_message",
                        messages=[{"type": "text", "content": msg}],
                        stream_response=False,
                    )

                events = list(sdk_client.agent_events.list(agent.key, session_key))
                assert len(events) >= 3, (
                    f"Expected at least 3 events after 3 turns, got {len(events)}"
                )
            finally:
                try:
                    sdk_client.agent_sessions.delete(agent.key, session_key)
                except Exception:
                    pass
        finally:
            try:
                sdk_client.agents.delete(agent.key)
            except Exception:
                pass
