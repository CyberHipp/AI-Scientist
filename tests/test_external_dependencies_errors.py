import types

import pytest

from ai_scientist.generate_ideas import search_for_papers
from ai_scientist.llm import get_response_from_llm


class _FakeResponse:
    def __init__(self, status_code, text):
        self.status_code = status_code
        self.text = text

    def json(self):
        return {}

    def raise_for_status(self):
        import requests

        raise requests.exceptions.HTTPError(f"Status: {self.status_code}", response=self)


def test_search_for_papers_raises_http_error(monkeypatch):
    def fake_get(url, headers=None, params=None):
        return _FakeResponse(status_code=401, text="Unauthorized")

    monkeypatch.setattr("ai_scientist.generate_ideas.requests.get", fake_get)

    with pytest.raises(Exception) as excinfo:
        search_for_papers("query", result_limit=1)

    assert "Status: 401" in str(excinfo.value)


def test_get_response_from_llm_unsupported_model():
    fake_client = types.SimpleNamespace()

    with pytest.raises(ValueError) as excinfo:
        get_response_from_llm("msg", fake_client, "unsupported-model", "sys")

    assert "not supported" in str(excinfo.value)
