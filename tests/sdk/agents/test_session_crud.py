"""
Agent Session CRUD Tests (SDK)

Tests for session create, get, update, delete operations and error cases.
"""

import uuid

import pytest
from vectara.errors import NotFoundError

from utils.waiters import wait_for


@pytest.mark.core
class TestSessionCrud:
    """Session create, get, update, delete operations."""

    def test_create_session_returns_key(self, sdk_client, sdk_shared_agent):
        """testCreateSession -- verify session key is returned."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        assert session.key is not None, "Session should have a key"
        assert session.agent_key == sdk_shared_agent

        try:
            sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
        except Exception:
            pass

    def test_create_session_default_values(self, sdk_client, sdk_shared_agent):
        """testCreateSessionDefaultValues -- verify defaults are set."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        try:
            assert session.enabled is True, f"New session should be enabled: {session.enabled}"
        finally:
            if session.key:
                try:
                    sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
                except Exception:
                    pass

    def test_create_session_agent_not_found(self, sdk_client):
        """testCreateSessionAgentNotFound -- non-existent agent returns 404."""
        with pytest.raises(NotFoundError):
            sdk_client.agent_sessions.create(f"nonexistent_{uuid.uuid4().hex[:8]}")

    def test_get_session(self, sdk_client, sdk_shared_agent):
        """testGetSession -- verify all expected fields present."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        try:
            retrieved = sdk_client.agent_sessions.get(sdk_shared_agent, session.key)
            assert retrieved.key == session.key
            assert retrieved.agent_key == sdk_shared_agent
            assert retrieved.enabled is not None
            assert retrieved.created_at is not None
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
            except Exception:
                pass

    def test_get_session_not_found(self, sdk_client, sdk_shared_agent):
        """testGetSessionNotFound -- non-existent session returns 404."""
        with pytest.raises(NotFoundError):
            sdk_client.agent_sessions.get(sdk_shared_agent, f"ase_fake_{uuid.uuid4().hex[:8]}")

    def test_delete_session(self, sdk_client, sdk_shared_agent):
        """testDeleteSession -- delete and verify 404."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)

        with pytest.raises(NotFoundError):
            sdk_client.agent_sessions.get(sdk_shared_agent, session.key)

    def test_delete_session_not_found(self, sdk_client, sdk_shared_agent):
        """testDeleteSessionNotFound -- delete non-existent returns 404."""
        with pytest.raises(NotFoundError):
            sdk_client.agent_sessions.delete(sdk_shared_agent, f"ase_fake_{uuid.uuid4().hex[:8]}")


@pytest.mark.core
class TestSessionUpdate:
    """Session update operations -- partial PATCH tests."""

    def test_update_session_description(self, sdk_client, sdk_shared_agent):
        """testUpdateSessionPartialUpdateDescriptionOnly."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        try:
            new_desc = f"Updated desc {uuid.uuid4().hex[:8]}"
            sdk_client.agent_sessions.update(sdk_shared_agent, session.key, description=new_desc)

            retrieved = sdk_client.agent_sessions.get(sdk_shared_agent, session.key)
            assert retrieved.description == new_desc, f"Description not persisted: {retrieved.description}"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
            except Exception:
                pass

    def test_update_session_enabled(self, sdk_client, sdk_shared_agent):
        """testUpdateSessionEnabledOnly -- disable then re-enable."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        try:
            sdk_client.agent_sessions.update(sdk_shared_agent, session.key, enabled=False)

            retrieved = sdk_client.agent_sessions.get(sdk_shared_agent, session.key)
            assert retrieved.enabled is False

            sdk_client.agent_sessions.update(sdk_shared_agent, session.key, enabled=True)

            retrieved2 = sdk_client.agent_sessions.get(sdk_shared_agent, session.key)
            assert retrieved2.enabled is True
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
            except Exception:
                pass

    def test_update_session_metadata(self, sdk_client, sdk_shared_agent):
        """testUpdateSessionMetadataOnly."""
        session = sdk_client.agent_sessions.create(
            sdk_shared_agent,
            metadata={"initial": "value"},
        )

        try:
            new_meta = {"priority": "high", "status": "escalated"}
            sdk_client.agent_sessions.update(sdk_shared_agent, session.key, metadata=new_meta)

            retrieved = sdk_client.agent_sessions.get(sdk_shared_agent, session.key)
            metadata = getattr(retrieved, "metadata", {}) or {}
            assert metadata.get("priority") == "high", f"Metadata not updated: {metadata}"
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
            except Exception:
                pass

    def test_update_session_nonexistent(self, sdk_client, sdk_shared_agent):
        """testUpdateSessionNonexistent -- update non-existent returns 404."""
        with pytest.raises(NotFoundError):
            sdk_client.agent_sessions.update(
                sdk_shared_agent,
                f"ase_fake_{uuid.uuid4().hex[:8]}",
                description="nope",
            )

    def test_update_session_with_special_characters(self, sdk_client, sdk_shared_agent):
        """testUpdateSessionWithSpecialCharacters -- unicode in description."""
        session = sdk_client.agent_sessions.create(sdk_shared_agent)

        try:
            sdk_client.agent_sessions.update(
                sdk_shared_agent,
                session.key,
                description="Description with accents: caf\u00e9, na\u00efve, r\u00e9sum\u00e9",
            )

            retrieved = sdk_client.agent_sessions.get(sdk_shared_agent, session.key)
            assert "caf\u00e9" in (retrieved.description or "")
        finally:
            try:
                sdk_client.agent_sessions.delete(sdk_shared_agent, session.key)
            except Exception:
                pass
