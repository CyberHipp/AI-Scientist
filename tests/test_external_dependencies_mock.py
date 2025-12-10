import types

import pytest

from ai_scientist.generate_ideas import search_for_papers
from ai_scientist.llm import get_response_from_llm


class _FakeResponse:
    def __init__(self, status_code=200, json_data=None, text="", raise_error=False):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
        self._raise_error = raise_error

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self._raise_error:
            import requests

            raise requests.exceptions.HTTPError(response=self)


def test_search_for_papers_uses_mocked_requests(monkeypatch):
    captured = {}

    def fake_get(url, headers=None, params=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["params"] = params
        return _FakeResponse(
            status_code=200,
            json_data={
                "total": 1,
                "data": [
                    {
                        "title": "Test Paper",
                        "authors": [{"name": "Doe"}],
                        "venue": "ArXiv",
                        "year": 2024,
                        "citationCount": 3,
                        "abstract": "Abstract text",
                    }
                ],
            },
            text="ok",
        )

    monkeypatch.setattr("ai_scientist.generate_ideas.requests.get", fake_get)

    papers = search_for_papers("transformers", result_limit=5)

    assert papers[0]["title"] == "Test Paper"
    assert captured["url"] == "https://api.semanticscholar.org/graph/v1/paper/search"
    # Ensure headers and params are forwarded to the external API
    assert "X-API-KEY" in captured["headers"]
    assert captured["params"]["limit"] == 5
    assert captured["params"]["query"] == "transformers"


def test_get_response_from_llm_with_fake_openai_client():
    class _FakeChoice:
        def __init__(self, content):
            self.message = types.SimpleNamespace(content=content)

    class _FakeChat:
        def __init__(self, content):
            self.choices = [_FakeChoice(content)]

        def create(self, **kwargs):  # pragma: no cover - signature compatibility
            return self

    class _FakeClient:
        def __init__(self, content):
            self.chat = types.SimpleNamespace(completions=_FakeChat(content))

    fake_client = _FakeClient("LLM response")

    content, _ = get_response_from_llm(
        "test message", fake_client, "gpt-4o-2024-05-13", "system msg"
    )

    assert content == "LLM response"
