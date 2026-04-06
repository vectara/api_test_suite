"""
LLM CRUD Tests

Core and regression tests for LLM configuration management.
"""

import os

import pytest


@pytest.mark.core
class TestLlmList:
    def test_list_llms(self, client):
        response = client.list_llms(limit=10)
        assert response.success, f"List LLMs failed: {response.status_code} - {response.data}"


@pytest.mark.regression
class TestLlmCrud:
    def test_create_and_delete_llm(self, client, unique_id):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        response = client.create_llm(
            name=f"test_llm_{unique_id}",
            model="gpt-4o-mini",
            uri="https://api.openai.com/v1/chat/completions",
            bearer_token=api_key,
        )
        if not response.success and ("quota" in str(response.data).lower() or "verify" in str(response.data).lower()):
            pytest.skip(f"LLM provider issue (quota/verification): {response.data}")
        assert response.success, f"Create LLM failed: {response.status_code} - {response.data}"

        llm_id = response.data.get("id")
        if llm_id:
            del_resp = client.delete_llm(llm_id)
            assert del_resp.success, f"Delete LLM failed: {del_resp.data}"
