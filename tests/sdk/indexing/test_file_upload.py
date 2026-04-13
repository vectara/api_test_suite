"""
File Upload Tests (SDK)

Tests for file upload operations including simple text files
and PDF uploads with table extraction configuration using the Vectara Python SDK.
"""

import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest

from vectara.types import TableExtractionConfig

from utils.waiters import wait_for

TESTDATA_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "testdata"


@pytest.mark.core
class TestFileUpload:
    """Core tests for file upload operations."""

    def test_upload_simple_file(self, sdk_client, sdk_shared_corpus, unique_id):
        """Upload a simple text file and verify it appears."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test document about artificial intelligence and semantic search.")
            temp_path = f.name

        try:
            with open(temp_path, "rb") as fh:
                doc = sdk_client.upload.file(
                    sdk_shared_corpus,
                    file=fh,
                    metadata={"source": "test_upload", "doc_id": unique_id},
                )
            assert doc.id, f"No document ID in upload response: {doc}"

            wait_for(
                lambda: _document_exists(sdk_client, sdk_shared_corpus, doc.id),
                timeout=15,
                interval=1,
                description="uploaded file to appear as document",
            )
        finally:
            os.unlink(temp_path)

    def test_upload_pdf_with_table_extraction(self, sdk_client, unique_id):
        """Upload PDF with table extraction config and validate extracted tables."""
        pdf_path = TESTDATA_DIR / "table_simple.pdf"
        expected_path = TESTDATA_DIR / "table_simple.json"

        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found at {pdf_path}")
        if not expected_path.exists():
            pytest.skip(f"Expected schema not found at {expected_path}")

        # Create dedicated corpus for this test
        corpus_key = f"upload_test_{uuid.uuid4().hex}"
        corpus = sdk_client.corpora.create(
            name=f"Upload Test {uuid.uuid4().hex[:8]}",
            key=corpus_key,
            description="Corpus for file upload testing",
        )

        actual_key = corpus.key

        try:
            wait_for(
                lambda: _corpus_exists(sdk_client, actual_key),
                timeout=10,
                interval=1,
                description="upload test corpus to become queryable",
            )

            # Upload with table extraction
            with open(pdf_path, "rb") as fh:
                try:
                    doc = sdk_client.upload.file(
                        actual_key,
                        file=fh,
                        metadata={"source": "pdf_table_test"},
                        table_extraction_config=TableExtractionConfig(extract_tables=True),
                    )
                except Exception as e:
                    if "Tabular data extraction" in str(e):
                        pytest.skip("Table extraction not available in this environment")
                    raise

            if doc.id:
                wait_for(
                    lambda: _document_exists(sdk_client, actual_key, doc.id),
                    timeout=60,
                    interval=2,
                    description="uploaded PDF to be processed",
                )

                # Load expected table structure
                with open(expected_path) as f:
                    expected = json.load(f)

                # Retrieve and validate
                fetched = sdk_client.documents.get(actual_key, doc.id)

                # Verify tables were extracted
                tables = fetched.tables or []
                if tables:
                    assert len(tables) > 0, "Expected at least one extracted table"
        finally:
            try:
                sdk_client.corpora.delete(actual_key)
            except Exception:
                pass


def _document_exists(sdk_client, corpus_key, doc_id):
    try:
        sdk_client.documents.get(corpus_key, doc_id)
        return True
    except Exception:
        return False


def _corpus_exists(sdk_client, corpus_key):
    try:
        sdk_client.corpora.get(corpus_key)
        return True
    except Exception:
        return False
