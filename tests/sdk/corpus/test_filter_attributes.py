"""
Corpus Filter Attribute Tests (SDK)

Core-level tests for creating corpora with custom filter attributes
(metadata configuration) using the Vectara Python SDK.
"""

import uuid

import pytest

from vectara.types import FilterAttribute


@pytest.mark.core
class TestFilterAttributes:
    """Core checks for corpus filter attribute configuration."""

    def test_create_corpus_with_metadata(self, sdk_client, unique_id):
        """Test creating a corpus with custom filter attributes."""
        corpus_key = f"meta_test_{uuid.uuid4().hex}"
        corpus = sdk_client.corpora.create(
            name=f"Metadata Corpus {unique_id}",
            key=corpus_key,
            description="Corpus with filter attributes",
            filter_attributes=[
                FilterAttribute(name="category", level="document", type="text"),
                FilterAttribute(name="priority", level="document", type="integer"),
            ],
        )

        # Verify filter attributes were persisted
        fetched = sdk_client.corpora.get(corpus.key)
        attrs = fetched.filter_attributes or []
        attr_names = [a.name for a in attrs]
        assert "category" in attr_names, f"Expected 'category' in filter attributes, got: {attr_names}"
        assert "priority" in attr_names, f"Expected 'priority' in filter attributes, got: {attr_names}"

        # Cleanup
        try:
            sdk_client.corpora.delete(corpus.key)
        except Exception:
            pass
