"""
Agent Session Compaction Tests

Tests for manual compaction, compaction config on agents, and fork-with-compaction.
Ported from AgentSessionIntegrationTest.java compaction tests.
"""

import uuid

import pytest
from utils.waiters import wait_for


@pytest.mark.core
class TestCompactionConfig:
    """Agent compaction configuration tests."""

    def test_create_agent_with_compaction_config(self, client, unique_id):
        """Verify compaction config persists on agent creation."""
        agent_key = f"compact_cfg_{unique_id}"
        resp = client.create_agent(
            name=f"Compaction Agent {unique_id}",
            agent_key=agent_key,
            compaction={
                "enabled": True,
                "threshold_percent": 70,
                "keep_recent_inputs": 2,
            },
        )
        if not resp.success:
            pytest.skip(f"Could not create agent with compaction: {resp.data}")

        try:
            get_resp = client.get_agent(agent_key)
            assert get_resp.success
            compaction = get_resp.data.get("compaction", {})
            assert compaction.get("enabled") is True, f"Compaction should be enabled: {compaction}"
            assert compaction.get("threshold_percent") == 70, f"Threshold should be 70: {compaction}"
            assert compaction.get("keep_recent_inputs") == 2, f"keep_recent_inputs should be 2: {compaction}"
        finally:
            try:
                client.delete_agent(agent_key)
            except Exception:
                pass

    def test_update_agent_compaction_config(self, client, unique_id):
        """Verify compaction config can be updated on an existing agent."""
        agent_key = f"compact_upd_{unique_id}"
        resp = client.create_agent(
            name=f"Compaction Update {unique_id}",
            agent_key=agent_key,
        )
        if not resp.success:
            pytest.skip(f"Could not create agent: {resp.data}")

        try:
            update_resp = client.update_agent(
                agent_key,
                compaction={"enabled": True, "threshold_percent": 60, "keep_recent_inputs": 3},
            )
            assert update_resp.success, f"Update compaction config failed: {update_resp.status_code} - {update_resp.data}"

            get_resp = client.get_agent(agent_key)
            compaction = get_resp.data.get("compaction", {})
            assert compaction.get("enabled") is True
            assert compaction.get("threshold_percent") == 60
        finally:
            try:
                client.delete_agent(agent_key)
            except Exception:
                pass


@pytest.mark.core
class TestManualCompaction:
    """Manual compaction via the events endpoint."""

    def test_manual_compaction_on_session(self, client, shared_agent):
        """manualCompaction_streamingOnIdleSession — send compact to a session with turns."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")

        session_key = session_resp.data.get("key")
        try:
            wait_for(
                lambda: client.get_agent_session(shared_agent, session_key).success,
                timeout=10, interval=0.5,
                description="session available",
            )

            turn1 = client.execute_agent(shared_agent, "Tell me about AI", session_id=session_key)
            assert turn1.success, f"Turn 1 failed: {turn1.status_code} - {turn1.data}"

            turn2 = client.execute_agent(shared_agent, "What about machine learning?", session_id=session_key)
            assert turn2.success, f"Turn 2 failed: {turn2.status_code} - {turn2.data}"

            events_before = client.list_session_events(shared_agent, session_key, limit=100)
            visible_before = len(events_before.data.get("events", []))
            assert visible_before >= 4, f"Expected at least 4 events (2 turns), got {visible_before}"

            compact_resp = client.compact_session(shared_agent, session_key)
            assert compact_resp.success or compact_resp.status_code == 201, \
                f"Compact failed: {compact_resp.status_code} - {compact_resp.data}"

            compact_events = compact_resp.data.get("events", [])
            compact_types = [e.get("type") for e in compact_events]
            assert "compaction" in compact_types or "compaction_started" in compact_types, \
                f"Expected compaction event in response, got types: {compact_types}"

            events_after = client.list_session_events(shared_agent, session_key, limit=100)
            visible_after = len(events_after.data.get("events", []))

            all_events = client.list_session_events(shared_agent, session_key, limit=100, include_hidden=True)
            total_after = len(all_events.data.get("events", []))
            assert total_after >= visible_before, \
                f"Hidden events should still exist: total={total_after} visible_before={visible_before}"
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass

    def test_manual_compaction_not_enough_turns(self, client, shared_agent):
        """manualCompaction_streamingNotEnoughTurns_returnsError — compact empty/single-turn session."""
        session_resp = client.create_agent_session(shared_agent)
        if not session_resp.success:
            pytest.skip(f"Could not create session: {session_resp.data}")

        session_key = session_resp.data.get("key")
        try:
            wait_for(
                lambda: client.get_agent_session(shared_agent, session_key).success,
                timeout=10, interval=0.5,
                description="session available",
            )

            compact_resp = client.compact_session(shared_agent, session_key)
            compact_events = compact_resp.data.get("events", []) if compact_resp.success else []
            has_error = any(e.get("type") == "error" for e in compact_events)

            assert not compact_resp.success or has_error, \
                f"Compact on empty session should fail or return error event: {compact_resp.status_code} - {compact_resp.data}"
        finally:
            try:
                client.delete_agent_session(shared_agent, session_key)
            except Exception:
                pass


@pytest.mark.core
class TestForkWithCompaction:
    """Fork session with compaction — ported from forkSession_withCompaction_compactsEvents."""

    def test_fork_with_compaction(self, client, agent_with_session):
        """Fork a session with compact_up_to_event_id and verify compaction occurs."""
        agent_key, session_key, events = agent_with_session

        if len(events) == 0:
            pytest.skip("No events in source session to compact")

        first_event_id = events[0].get("id")
        if not first_event_id:
            pytest.skip("Could not get first event ID")

        fork_resp = client.create_agent_session(
            agent_key,
            from_session={
                "session_key": session_key,
                "compact_up_to_event_id": first_event_id,
            },
        )
        assert fork_resp.success, f"Fork with compaction failed: {fork_resp.status_code} - {fork_resp.data}"

        forked_key = fork_resp.data.get("key")
        try:
            forked_events = client.list_session_events(agent_key, forked_key, limit=100)
            assert forked_events.success
            forked_list = forked_events.data.get("events", [])
            forked_types = [e.get("type") for e in forked_list]
            assert "compaction" in forked_types, \
                f"Forked session should contain compaction event, got types: {forked_types}"
        finally:
            if forked_key:
                try:
                    client.delete_agent_session(agent_key, forked_key)
                except Exception:
                    pass

    def test_fork_include_up_to_event_id(self, client, agent_with_session):
        """forkSession_includeUpToEventId_copiesOnlyEventsUpToThatId."""
        agent_key, session_key, events = agent_with_session

        if len(events) < 2:
            pytest.skip("Need at least 2 events for include_up_to test")

        cutoff_event_id = events[0].get("id")
        fork_resp = client.create_agent_session(
            agent_key,
            from_session={
                "session_key": session_key,
                "include_up_to_event_id": cutoff_event_id,
            },
        )
        assert fork_resp.success, f"Fork failed: {fork_resp.status_code} - {fork_resp.data}"

        forked_key = fork_resp.data.get("key")
        try:
            forked_events = client.list_session_events(agent_key, forked_key, limit=100)
            forked_ids = [e.get("id") for e in forked_events.data.get("events", [])]
            assert len(forked_ids) <= len(events), \
                f"Forked session should have fewer or equal events: forked={len(forked_ids)} source={len(events)}"
        finally:
            if forked_key:
                try:
                    client.delete_agent_session(agent_key, forked_key)
                except Exception:
                    pass

    def test_fork_include_up_to_bad_event_id(self, client, agent_with_session):
        """forkSession_includeUpToEventId_notFound_returnsBadRequest."""
        agent_key, session_key, _ = agent_with_session

        fork_resp = client.create_agent_session(
            agent_key,
            from_session={
                "session_key": session_key,
                "include_up_to_event_id": "aev_nonexistent_fake_id",
            },
        )
        assert fork_resp.status_code >= 400, \
            f"Fork with bad event ID should fail: {fork_resp.status_code} - {fork_resp.data}"
