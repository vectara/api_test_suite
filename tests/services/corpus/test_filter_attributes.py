"""
Corpus Filter Attribute Tests

Core-level tests for creating corpora with custom filter attributes
(metadata configuration).
"""

import pytest


@pytest.mark.core
class TestFilterAttributes:
    """Core checks for corpus filter attribute configuration."""

    def test_create_corpus_with_metadata(self, client, unique_id):
        """Test creating a corpus with custom filter attributes."""
        import uuid
        corpus_key = f"meta_test_{uuid.uuid4().hex}"
        response = client.create_corpus(
            name=f"Metadata Corpus {unique_id}",
            key=corpus_key,
            description="Corpus with filter attributes",
            filter_attributes=[
                {
                    "name": "category",
                    "level": "document",
                    "type": "text",
                },
                {
                    "name": "priority",
                    "level": "document",
                    "type": "integer",
                },
            ],
        )

        assert response.success, (
            f"Corpus creation with metadata failed: {response.status_code} - {response.data}"
        )

        # Cleanup using the actual key
        actual_key = response.data.get("key")
        if actual_key:
            try:
                client.delete_corpus(actual_key)
            except Exception:
                pass
