"""
LLM CRUD Tests (SDK)

Core and regression tests for LLM configuration management.
"""

import os

import pytest

from vectara.types import CreateLlmRequest_OpenaiCompatible, RemoteAuth_Bearer


@pytest.mark.core
class TestLlmList:
    def test_list_llms(self, sdk_client):
        pager = sdk_client.llms.list(limit=10)
        llms = list(pager)
        assert isinstance(llms, list), f"Expected list, got {type(llms)}"
        assert len(llms) > 0, "Expected at least one LLM in the list"


@pytest.mark.regression
class TestLlmCrud:
    def test_create_and_delete_llm(self, sdk_client, unique_id):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        try:
            llm = sdk_client.llms.create(
                request=CreateLlmRequest_OpenaiCompatible(
                    name=f"test_llm_{unique_id}",
                    model="gpt-4o-mini",
                    uri="https://api.openai.com/v1/chat/completions",
                    auth=RemoteAuth_Bearer(token=api_key),
                    description="Test LLM created by SDK test suite",
                ),
            )
        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "verify" in err_msg:
                pytest.skip(f"LLM provider issue (quota/verification): {e}")
            raise

        llm_id = getattr(llm, "id", None)
        assert llm_id, f"No LLM ID in create response"
        assert llm.name == f"test_llm_{unique_id}", f"LLM name mismatch: {llm.name}"

        sdk_client.llms.delete(llm_id)
