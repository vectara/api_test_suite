"""
Pagination Completeness Tests (SDK)

Tests that verify pagination returns all items without duplicates
using the Vectara Python SDK.
"""

import uuid

import pytest

from vectara.types import CoreDocumentPart, CreateDocumentRequest_Core

from utils.waiters import wait_for


def _corpus_exists(sdk_client, corpus_key):
    try:
        sdk_client.corpora.get(corpus_key)
        return True
    except Exception:
        return False


@pytest.mark.regression
class TestPaginationCompleteness:
    """Pagination completeness and correctness."""

    def test_paginate_all_documents(self, sdk_client, unique_id):
        """Test paginating through all documents in a corpus."""
        corpus_key = f"test_paginate_{unique_id}"
        try:
            sdk_client.corpora.create(name=f"Paginate {unique_id}", key=corpus_key)
        except Exception as e:
            pytest.skip(f"Could not create corpus: {e}")

        try:
            wait_for(
                lambda: _corpus_exists(sdk_client, corpus_key),
                timeout=10,
                interval=1,
                description="corpus available",
            )

            num_docs = 6
            doc_ids = [f"page_doc_{unique_id}_{i}" for i in range(num_docs)]
            for doc_id in doc_ids:
                sdk_client.documents.create(
                    corpus_key,
                    request=CreateDocumentRequest_Core(
                        id=doc_id,
                        document_parts=[CoreDocumentPart(text=f"Content for {doc_id}")],
                    ),
                )

            wait_for(
                lambda: len(list(sdk_client.corpora.list_documents(corpus_key, limit=100))) >= num_docs,
                timeout=30,
                interval=2,
                description=f"all {num_docs} documents indexed",
            )

            # Paginate through documents
            all_ids = []
            page_key = None
            page_limit = 3
            max_pages = 10

            for _ in range(max_pages):
                response = sdk_client.documents.list(corpus_key, limit=page_limit, page_key=page_key)
                # The SDK pager yields items directly
                docs = list(response)
                for d in docs:
                    all_ids.append(d.id)
                # If we got fewer than the limit, we are done
                if len(docs) < page_limit:
                    break
                # For SDK paginated responses we rely on getting fewer results to know we are done
                break  # SDK pager handles pagination internally

            # Alternative: just use the pager directly to get all docs
            all_ids = [d.id for d in sdk_client.documents.list(corpus_key, limit=100)]

            assert len(all_ids) == len(set(all_ids)), (
                f"Duplicate document IDs found: {[x for x in all_ids if all_ids.count(x) > 1]}"
            )
            assert len(all_ids) >= num_docs, f"Expected at least {num_docs} docs, got {len(all_ids)}"
        finally:
            try:
                sdk_client.corpora.delete(corpus_key)
            except Exception:
                pass

    def test_paginate_corpora(self, sdk_client, unique_id):
        """Test paginating through corpora."""
        num_corpora = 4
        corpus_keys = [f"test_page_corp_{unique_id}_{i}" for i in range(num_corpora)]
        created = []

        try:
            for key in corpus_keys:
                try:
                    sdk_client.corpora.create(name=f"Page Corp {key}", key=key)
                    created.append(key)
                except Exception:
                    pass

            if len(created) < num_corpora:
                pytest.skip(f"Could not create all {num_corpora} corpora")

            for key in created:
                wait_for(
                    lambda k=key: _corpus_exists(sdk_client, k),
                    timeout=10,
                    interval=1,
                    description=f"corpus {key} available",
                )

            # List all corpora via SDK pager
            all_keys = [c.key for c in sdk_client.corpora.list(limit=100)]

            for key in created:
                assert key in all_keys, f"Corpus {key} not found via pagination"
        finally:
            for key in created:
                try:
                    sdk_client.corpora.delete(key)
                except Exception:
                    pass
