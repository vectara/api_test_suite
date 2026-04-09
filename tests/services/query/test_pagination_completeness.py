"""
Pagination Completeness Tests

Tests that verify pagination returns all items without duplicates.
"""

import uuid

import pytest
from utils.waiters import wait_for


@pytest.mark.regression
class TestPaginationCompleteness:
    """Pagination completeness and correctness."""

    def test_paginate_all_documents(self, client, unique_id):
        """Test paginating through all documents in a corpus."""
        corpus_key = f"test_paginate_{unique_id}"
        create_resp = client.create_corpus(name=f"Paginate {unique_id}", key=corpus_key)
        if not create_resp.success:
            pytest.skip(f"Could not create corpus: {create_resp.data}")

        try:
            wait_for(
                lambda: client.get_corpus(corpus_key).success,
                timeout=10, interval=1,
                description="corpus available",
            )

            num_docs = 6
            doc_ids = [f"page_doc_{unique_id}_{i}" for i in range(num_docs)]
            for doc_id in doc_ids:
                resp = client.index_document(corpus_key, doc_id, f"Content for {doc_id}")
                assert resp.success, f"Index {doc_id} failed: {resp.status_code}"

            wait_for(
                lambda: len(
                    client.list_documents(corpus_key, limit=100).data.get("documents", [])
                ) >= num_docs,
                timeout=30, interval=2,
                description=f"all {num_docs} documents indexed",
            )

            all_ids = []
            page_key = None
            page_limit = 3
            max_pages = 10

            for _ in range(max_pages):
                list_resp = client.list_documents(corpus_key, limit=page_limit, page_key=page_key)
                assert list_resp.success, f"List failed: {list_resp.status_code}"
                docs = list_resp.data.get("documents", [])
                for d in docs:
                    all_ids.append(d.get("id"))

                page_key = list_resp.data.get("metadata", {}).get("page_key")
                if not page_key:
                    break

            assert len(all_ids) == len(set(all_ids)), \
                f"Duplicate document IDs found: {[x for x in all_ids if all_ids.count(x) > 1]}"
            assert len(all_ids) >= num_docs, \
                f"Expected at least {num_docs} docs, got {len(all_ids)}"
        finally:
            try:
                client.delete_corpus(corpus_key)
            except Exception:
                pass

    def test_paginate_corpora(self, client, unique_id):
        """Test paginating through corpora."""
        num_corpora = 4
        corpus_keys = [f"test_page_corp_{unique_id}_{i}" for i in range(num_corpora)]
        created = []

        try:
            for key in corpus_keys:
                resp = client.create_corpus(name=f"Page Corp {key}", key=key)
                if resp.success:
                    created.append(key)

            if len(created) < num_corpora:
                pytest.skip(f"Could not create all {num_corpora} corpora")

            for key in created:
                wait_for(
                    lambda k=key: client.get_corpus(k).success,
                    timeout=10, interval=1,
                    description=f"corpus {key} available",
                )

            all_keys = []
            page_key = None
            for _ in range(10):
                list_resp = client.list_corpora(limit=2, page_key=page_key)
                assert list_resp.success
                corpora = list_resp.data.get("corpora", [])
                for c in corpora:
                    all_keys.append(c.get("key"))
                page_key = list_resp.data.get("metadata", {}).get("page_key")
                if not page_key:
                    break

            for key in created:
                assert key in all_keys, f"Corpus {key} not found via pagination"
        finally:
            for key in created:
                try:
                    client.delete_corpus(key)
                except Exception:
                    pass
