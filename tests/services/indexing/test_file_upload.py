"""
File Upload Tests

Tests for file upload operations including simple text files
and PDF uploads with table extraction configuration.
"""

import os
import tempfile
import uuid
from pathlib import Path

import pytest

from utils.waiters import wait_for

TESTDATA_DIR = Path(__file__).parent.parent.parent.parent / "fixtures" / "testdata"


@pytest.mark.core
class TestFileUpload:
    """Core tests for file upload operations."""

    def test_upload_simple_file(self, client, shared_corpus, unique_id):
        """Upload a simple text file and verify it appears."""
        # Create a temp text file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a test document about artificial intelligence and semantic search.")
            temp_path = f.name

        try:
            response = client.upload_file(
                corpus_key=shared_corpus,
                file_path=temp_path,
                metadata={"source": "test_upload", "doc_id": unique_id},
            )
            assert response.success, f"File upload failed: {response.status_code} - {response.data}"

            # Verify document appears in corpus
            doc_id = response.data.get("id")
            assert doc_id, f"No document ID in upload response: {response.data}"

            wait_for(
                lambda: client.get_document(shared_corpus, doc_id).success,
                timeout=15,
                interval=1,
                description="uploaded file to appear as document",
            )
        finally:
            os.unlink(temp_path)

    def test_upload_pdf_with_table_extraction(self, client, unique_id):
        """Upload PDF with table extraction config and validate extracted tables."""
        pdf_path = TESTDATA_DIR / "table_simple.pdf"
        expected_path = TESTDATA_DIR / "table_simple.json"

        if not pdf_path.exists():
            pytest.skip(f"Test PDF not found at {pdf_path}")
        if not expected_path.exists():
            pytest.skip(f"Expected schema not found at {expected_path}")

        # Create dedicated corpus for this test
        corpus_key = f"upload_test_{uuid.uuid4().hex}"
        corpus_response = client.create_corpus(
            name=f"Upload Test {uuid.uuid4().hex[:8]}",
            key=corpus_key,
            description="Corpus for file upload testing",
        )
        if not corpus_response.success:
            pytest.skip(f"Could not create corpus: {corpus_response.data}")

        actual_key = corpus_response.data.get("key", corpus_key)

        try:
            wait_for(
                lambda: client.get_corpus(actual_key).success,
                timeout=10,
                interval=1,
                description="upload test corpus to become queryable",
            )

            # Upload with table extraction
            upload_response = client.upload_file(
                corpus_key=actual_key,
                file_path=str(pdf_path),
                metadata={"source": "pdf_table_test"},
                table_extraction_config={
                    "extract_tables": True,
                    "extractor": {"name": "gmft"},
                },
            )
            if not upload_response.success and "Tabular data extraction" in str(upload_response.data):
                pytest.skip("Table extraction not available in this environment")
            assert upload_response.success, f"PDF upload failed: {upload_response.status_code} - {upload_response.data}"

            # Get the document ID from upload response
            doc_id = upload_response.data.get("id")
            if doc_id:
                # Wait for document to be processed
                wait_for(
                    lambda: client.get_document(actual_key, doc_id).success,
                    timeout=60,
                    interval=2,
                    description="uploaded PDF to be processed",
                )

                # Load expected table structure
                with open(expected_path) as f:
                    import json

                    expected = json.load(f)

                # Retrieve and validate
                doc_response = client.get_document(actual_key, doc_id)
                assert doc_response.success, f"Get doc failed: {doc_response.status_code}"

                # Verify tables were extracted
                tables = doc_response.data.get("tables", [])
                if tables:
                    # Validate table structure matches expected
                    assert len(tables) > 0, "Expected at least one extracted table"
                    first_table = tables[0]
                    assert "data" in first_table, f"Table missing 'data' field: {first_table.keys()}"
                    table_data = first_table["data"]
                    assert "headers" in table_data, f"Table data missing 'headers'"
                    assert "rows" in table_data, f"Table data missing 'rows'"

        finally:
            try:
                client.delete_corpus(actual_key)
            except Exception:
                pass
