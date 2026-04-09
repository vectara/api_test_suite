"""End-to-end indexing and query workflow.

Creates a corpus, indexes documents, queries them with semantic search
and RAG summarization, then cleans up.
"""

import uuid
import pytest
from utils.waiters import wait_for


@pytest.mark.workflow
class TestIndexQueryFlow:

    def test_full_indexing_and_query_flow(self, client):
        """Create corpus -> index docs -> query -> RAG summary -> cleanup."""
        corpus_key = f"workflow_{uuid.uuid4().hex}"

        # Step 1: Create corpus
        corpus_resp = client.create_corpus(
            name=f"Workflow Test {uuid.uuid4().hex[:8]}",
            key=corpus_key,
            description="E2E workflow test corpus",
        )
        assert corpus_resp.success, f"Create corpus failed: {corpus_resp.data}"
        actual_key = corpus_resp.data.get("key", corpus_key)

        try:
            wait_for(
                lambda: client.get_corpus(actual_key).success,
                timeout=10, interval=1,
                description="workflow corpus to become queryable",
            )

            # Step 2: Index documents
            doc_ids = []
            docs = [
                {"id": f"wf_doc_{uuid.uuid4().hex[:8]}", "text": "Machine learning enables computers to learn from data without explicit programming.", "metadata": {"topic": "ml"}},
                {"id": f"wf_doc_{uuid.uuid4().hex[:8]}", "text": "Neural networks are inspired by biological brain structures and excel at pattern recognition.", "metadata": {"topic": "nn"}},
                {"id": f"wf_doc_{uuid.uuid4().hex[:8]}", "text": "Natural language processing allows machines to understand and generate human language.", "metadata": {"topic": "nlp"}},
            ]
            for doc in docs:
                resp = client.index_document(
                    corpus_key=actual_key,
                    document_id=doc["id"],
                    text=doc["text"],
                    metadata=doc["metadata"],
                )
                assert resp.success, f"Index doc {doc['id']} failed: {resp.data}"
                doc_ids.append(doc["id"])

            # Step 3: Wait for indexing
            wait_for(
                lambda: len(client.list_documents(actual_key, limit=10).data.get("documents", [])) >= 3,
                timeout=15, interval=1,
                description="all 3 docs to be indexed",
            )

            # Step 4: Semantic search
            query_resp = client.query(
                corpus_key=actual_key,
                query_text="How do machines learn from data?",
                limit=5,
            )
            assert query_resp.success, f"Query failed: {query_resp.data}"
            results = query_resp.data.get("search_results", query_resp.data.get("results", []))
            assert len(results) > 0, "Expected at least one search result"

            # Verify top result relates to indexed content
            top_text = results[0].get("text", "").lower()
            assert any(term in top_text for term in ["learn", "data", "machine", "neural", "language"]), (
                f"Top result doesn't relate to indexed docs: {top_text[:200]}"
            )

            # Step 5: RAG summary
            summary_resp = client.query_with_summary(
                corpus_key=actual_key,
                query_text="Explain how AI works",
                max_results=3,
            )
            assert summary_resp.success, f"Summary query failed: {summary_resp.data}"
            has_summary = "summary" in summary_resp.data or "generation" in summary_resp.data
            assert has_summary, f"Expected summary in response: {list(summary_resp.data.keys())}"

            summary_text = summary_resp.data.get("summary", summary_resp.data.get("generation", ""))
            if isinstance(summary_text, dict):
                summary_text = summary_text.get("text", str(summary_text))
            assert len(str(summary_text)) > 10, f"Summary too short or empty: {summary_text}"

        finally:
            # Cleanup in reverse order
            for doc_id in doc_ids:
                try:
                    client.delete_document(actual_key, doc_id)
                except Exception:
                    pass
            try:
                client.delete_corpus(actual_key)
            except Exception:
                pass
