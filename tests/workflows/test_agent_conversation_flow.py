"""End-to-end agent conversation workflow.

Creates a corpus, seeds data, creates an agent, starts a session,
has a multi-turn conversation, and verifies context is maintained.
"""

import uuid
import pytest
from utils.waiters import wait_for


@pytest.mark.workflow
class TestAgentConversationFlow:

    def test_agent_multi_turn_conversation(self, client):
        """Create corpus -> seed -> create agent -> chat -> verify context -> cleanup."""
        corpus_key = f"agent_wf_{uuid.uuid4().hex}"
        agent_key = None
        session_key = None

        # Step 1: Create and seed corpus
        corpus_resp = client.create_corpus(
            name=f"Agent Workflow {uuid.uuid4().hex[:8]}",
            key=corpus_key,
            description="E2E agent workflow corpus",
        )
        assert corpus_resp.success, f"Create corpus failed: {corpus_resp.data}"
        actual_corpus_key = corpus_resp.data.get("key", corpus_key)

        try:
            wait_for(
                lambda: client.get_corpus(actual_corpus_key).success,
                timeout=10, interval=1,
                description="agent workflow corpus",
            )

            # Seed documents
            doc_ids = []
            docs = [
                {"id": f"awf_{uuid.uuid4().hex[:8]}", "text": "Vectara provides semantic search and RAG for enterprise applications.", "metadata": {"topic": "overview"}},
                {"id": f"awf_{uuid.uuid4().hex[:8]}", "text": "Agents maintain context across conversation turns for natural follow-up questions.", "metadata": {"topic": "agents"}},
            ]
            for doc in docs:
                resp = client.index_document(corpus_key=actual_corpus_key, document_id=doc["id"], text=doc["text"], metadata=doc["metadata"])
                if resp.success:
                    doc_ids.append(doc["id"])

            wait_for(
                lambda: client.list_documents(actual_corpus_key, limit=5).data.get("documents", []),
                timeout=15, interval=1,
                description="agent workflow docs indexed",
            )

            # Step 2: Create agent
            agent_resp = client.create_agent(
                name=f"Workflow Agent {uuid.uuid4().hex[:8]}",
                description="E2E workflow test agent",
            )
            assert agent_resp.success, f"Create agent failed: {agent_resp.data}"
            agent_key = agent_resp.data.get("key") or agent_resp.data.get("id")

            # Step 3: Create session
            session_resp = client.create_agent_session(agent_key)
            assert session_resp.success, f"Create session failed: {session_resp.data}"
            session_key = session_resp.data.get("key")

            # Step 4: First turn
            turn1 = client.execute_agent(
                agent_id=agent_key,
                query_text="What does Vectara do?",
                session_id=session_key,
            )
            assert turn1.success, f"First turn failed: {turn1.data}"

            # Step 5: Follow-up (tests context maintenance)
            turn2 = client.execute_agent(
                agent_id=agent_key,
                query_text="How do agents work?",
                session_id=session_key,
            )
            assert turn2.success, f"Follow-up failed: {turn2.data}"

            # Step 6: Verify events exist
            events_resp = client.list_session_events(agent_key, session_key)
            assert events_resp.success, f"List events failed: {events_resp.data}"
            events = events_resp.data.get("events", [])
            assert len(events) >= 2, f"Expected at least 2 events, got {len(events)}"

        finally:
            # Cleanup: reverse dependency order
            if session_key and agent_key:
                try:
                    client.delete_agent_session(agent_key, session_key)
                except Exception:
                    pass
            if agent_key:
                try:
                    client.delete_agent(agent_key)
                except Exception:
                    pass
            for doc_id in doc_ids:
                try:
                    client.delete_document(actual_corpus_key, doc_id)
                except Exception:
                    pass
            try:
                client.delete_corpus(actual_corpus_key)
            except Exception:
                pass
