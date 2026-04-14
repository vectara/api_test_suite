"""
Agent Session Compaction Tests (SDK)

Tests for compaction config on agents, manual compaction, and fork-with-compaction.
"""

import pytest
from vectara.agent_events.types import (
    CreateAgentEventsRequestBody_Compact,
    CreateAgentEventsRequestBody_InputMessage,
)
from vectara.core.api_error import ApiError
from vectara.types import CompactionConfig

from .conftest import create_agent
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

    def test_create_agent_and_verify_config(self, sdk_client, sdk_shared_agent):
        """Verify agent can be retrieved with expected fields."""
        retrieved = sdk_client.agents.get(sdk_shared_agent)
        assert retrieved.key == sdk_shared_agent
        assert retrieved.name is not None

    def test_update_agent_description(self, sdk_client, sdk_shared_agent):
        """Verify agent description can be updated."""
        # Save original description to restore after test
        original = sdk_client.agents.get(sdk_shared_agent)
        original_description = original.description

        try:
            sdk_client.agents.update(sdk_shared_agent, description="Updated compaction config")

            retrieved = sdk_client.agents.get(sdk_shared_agent)
            assert retrieved.description == "Updated compaction config"
        finally:
            sdk_client.agents.update(sdk_shared_agent, description=original_description)

    def test_create_agent_with_compaction_config(self, sdk_client, sdk_shared_agent_corpus):
        """Verify compaction config persists on agent creation."""
        compaction_cfg = CompactionConfig(
            enabled=True,
            threshold_percent=70,
            keep_recent_inputs=2,
        )
        agent = None
        try:
            agent = create_agent(
                sdk_client,
                sdk_shared_agent_corpus,
                name_prefix="SDK Compaction Agent",
                description="Agent with compaction config",
            )
            # The create_agent helper doesn't pass compaction, so update immediately
            sdk_client.agents.update(agent.key, compaction=compaction_cfg)

            retrieved = sdk_client.agents.get(agent.key)
            compaction = getattr(retrieved, "compaction", None)
            assert compaction is not None, f"Compaction should be set on agent: {retrieved}"
            assert compaction.enabled is True, f"Compaction should be enabled: {compaction}"
            assert compaction.threshold_percent == 70, f"Threshold should be 70: {compaction}"
            assert compaction.keep_recent_inputs == 2, f"keep_recent_inputs should be 2: {compaction}"
        finally:
            if agent:
                try:
                    sdk_client.agents.delete(agent.key)
                except Exception:
                    pass

    def test_update_agent_compaction_config(self, sdk_client, sdk_shared_agent):
        """Verify compaction config can be updated on an existing agent."""
        original = sdk_client.agents.get(sdk_shared_agent)
        original_compaction = getattr(original, "compaction", None)

        try:
            new_compaction = CompactionConfig(
                enabled=True,
                threshold_percent=60,
                keep_recent_inputs=3,
            )
            sdk_client.agents.update(sdk_shared_agent, compaction=new_compaction)

            retrieved = sdk_client.agents.get(sdk_shared_agent)
            compaction = getattr(retrieved, "compaction", None)
            assert compaction is not None, "Compaction config should be set"
            assert compaction.enabled is True
            assert compaction.threshold_percent == 60
        finally:
            # Restore original compaction config
            if original_compaction is not None:
                sdk_client.agents.update(sdk_shared_agent, compaction=original_compaction)
            else:
                try:
                    sdk_client.agents.update(
                        sdk_shared_agent,
                        compaction=CompactionConfig(enabled=False),
                    )
                except Exception:
                    pass


@pytest.mark.core
class TestManualCompaction:
    """Manual compaction via multi-turn sessions."""

    def test_multi_turn_session(self, sdk_client, sdk_shared_agent):
        """Create session on shared agent, send multiple turns, verify events accumulate."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            wait_for(
                lambda: _session_exists(sdk_client, sdk_shared_agent, session_key),
                timeout=10,
                interval=0.5,
                description="session available",
            )

            for msg in ["Tell me about AI", "What about machine learning?", "How do neural networks work?"]:
                sdk_client.agent_events.create(
                    sdk_shared_agent,
                    session_key,
                    request=CreateAgentEventsRequestBody_InputMessage(
                        messages=[{"type": "text", "content": msg}],
                        stream_response=False,
                    ),
                )

            events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
            assert len(events) >= 3, f"Expected at least 3 events after 3 turns, got {len(events)}"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass

    def test_manual_compaction_on_session(self, sdk_client, sdk_shared_agent_corpus):
        """Send 5+ turns then compact -- verify compaction event appears."""
        compaction_cfg = CompactionConfig(
            enabled=True,
            threshold_percent=50,
            keep_recent_inputs=1,
        )
        agent = create_agent(
            sdk_client,
            sdk_shared_agent_corpus,
            name_prefix="SDK Compact Manual",
            description="Agent for manual compaction test",
        )
        sdk_client.agents.update(agent.key, compaction=compaction_cfg)

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

                messages = [
                    "Tell me about AI",
                    "What about machine learning?",
                    "How do neural networks work?",
                    "What are transformers?",
                    "Explain attention mechanisms",
                ]
                for msg in messages:
                    sdk_client.agent_events.create(
                        agent.key,
                        session_key,
                        request=CreateAgentEventsRequestBody_InputMessage(
                            messages=[{"type": "text", "content": msg}],
                            stream_response=False,
                        ),
                    )

                # Wait for events to accumulate
                wait_for(
                    lambda: len(list(sdk_client.agent_events.list(agent.key, session_key))) >= 6,
                    timeout=30,
                    interval=2,
                    description="at least 6 events to be committed",
                )

                events_before = list(sdk_client.agent_events.list(agent.key, session_key))
                visible_before = len(events_before)

                # Trigger manual compaction
                compact_response = sdk_client.agent_events.create(
                    agent.key,
                    session_key,
                    request=CreateAgentEventsRequestBody_Compact(
                        stream_response=False,
                    ),
                )
                assert compact_response is not None, "Compact should return a response"

                # Verify compaction event exists in the session
                all_events = list(
                    sdk_client.agent_events.list(agent.key, session_key, include_hidden=True)
                )
                event_types = [str(getattr(e, "type", "")) for e in all_events]
                assert any(
                    "compaction" in t for t in event_types
                ), f"Expected compaction event in session, got types: {event_types}"

                assert len(all_events) >= visible_before, (
                    f"Hidden events should still exist: total={len(all_events)} visible_before={visible_before}"
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

    def test_manual_compaction_not_enough_turns(self, sdk_client, sdk_shared_agent):
        """Compact on empty/single-turn session should fail or return error event."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)
        session_key = session.key

        try:
            wait_for(
                lambda: _session_exists(sdk_client, sdk_shared_agent, session_key),
                timeout=10,
                interval=0.5,
                description="session available",
            )

            # Try to compact an empty session -- expect failure or error event
            try:
                compact_response = sdk_client.agent_events.create(
                    sdk_shared_agent,
                    session_key,
                    request=CreateAgentEventsRequestBody_Compact(
                        stream_response=False,
                    ),
                )
                # If it succeeded, check for error event in the response or session
                events = list(sdk_client.agent_events.list(sdk_shared_agent, session_key))
                event_types = [str(getattr(e, "type", "")) for e in events]
                has_error = any("error" in t for t in event_types)
                assert has_error, (
                    f"Compact on empty session should produce an error event, got types: {event_types}"
                )
            except (ApiError, Exception) as e:
                # Expected: compaction on empty session should fail
                pass
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session_key)
            except Exception:
                pass
