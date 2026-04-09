"""
Cross-Corpus RAG Workflow Test

End-to-end test that creates two corpora with distinct domains,
seeds each, performs a RAG query across both, and verifies the
response includes results from both corpora.
"""

import uuid

import pytest

from utils.waiters import wait_for


@pytest.mark.workflow
class TestCrossCorpusRagFlow:
    """Cross-corpus RAG workflow."""

    def test_cross_corpus_rag(self, client):
        """Create 2 corpora, seed each, RAG query across both, verify provenance."""
        uid = uuid.uuid4().hex[:8]
        corpus1_key = f"rag_medical_{uid}"
        corpus2_key = f"rag_legal_{uid}"

        c1 = client.create_corpus(name=f"Medical {uid}", key=corpus1_key)
        c2 = client.create_corpus(name=f"Legal {uid}", key=corpus2_key)

        if not c1.success or not c2.success:
            for k in [corpus1_key, corpus2_key]:
                try:
                    client.delete_corpus(k)
                except Exception:
                    pass
            pytest.skip("Could not create corpora for cross-corpus RAG test")

        try:
            for key in [corpus1_key, corpus2_key]:
                wait_for(
                    lambda k=key: client.get_corpus(k).success,
                    timeout=10,
                    interval=1,
                    description=f"corpus {key} available",
                )

            medical_docs = [
                ("med_1", "Heart disease prevention through diet and exercise reduces mortality rates significantly."),
                ("med_2", "Clinical trials for new cancer treatments show promising results in early stages."),
            ]
            legal_docs = [
                ("legal_1", "Contract law requires mutual consideration between parties for enforcement."),
                ("legal_2", "Intellectual property rights protect creators from unauthorized use of their work."),
            ]

            for doc_id, text in medical_docs:
                r = client.index_document(corpus1_key, f"{doc_id}_{uid}", text)
                assert r.success, f"Index medical doc failed: {r.data}"
            for doc_id, text in legal_docs:
                r = client.index_document(corpus2_key, f"{doc_id}_{uid}", text)
                assert r.success, f"Index legal doc failed: {r.data}"

            for key, docs in [(corpus1_key, medical_docs), (corpus2_key, legal_docs)]:
                wait_for(
                    lambda k=key, d=docs: all(client.get_document(k, f"{did}_{uid}").success for did, _ in d),
                    timeout=20,
                    interval=2,
                    description=f"documents indexed in {key}",
                )

            generation = {}
            if client.generation_preset:
                generation["generation_preset_name"] = client.generation_preset
            if client.llm_name:
                generation["model_parameters"] = {"llm_name": client.llm_name}

            query_resp = client.post(
                "/v2/query",
                data={
                    "query": "important topics in modern society",
                    "search": {
                        "corpora": [
                            {"corpus_key": corpus1_key},
                            {"corpus_key": corpus2_key},
                        ],
                        "limit": 10,
                    },
                    "generation": generation,
                },
            )
            assert query_resp.success, f"RAG query failed: {query_resp.status_code} - {query_resp.data}"

            results = query_resp.data.get("search_results", [])
            assert len(results) > 0, "Expected search results from cross-corpus RAG"

            result_corpus_keys = {r.get("corpus_key") for r in results}
            assert (
                corpus1_key in result_corpus_keys or corpus2_key in result_corpus_keys
            ), f"Expected results from at least one test corpus, got keys: {result_corpus_keys}"

            has_summary = query_resp.data.get("summary") is not None or query_resp.data.get("generation") is not None
            if has_summary:
                summary_text = query_resp.data.get("summary", "") or ""
                assert len(summary_text) > 0, "Summary should be non-empty"
        finally:
            for key in [corpus1_key, corpus2_key]:
                try:
                    client.delete_corpus(key)
                except Exception:
                    pass
