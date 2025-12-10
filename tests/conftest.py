import os
import sys
import types

# Ensure project root is on sys.path for module imports in tests
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Provide a lightweight stub for backoff when the dependency is unavailable in the test environment.
if "backoff" not in sys.modules:
    backoff_stub = types.SimpleNamespace()

    def _identity_decorator(*args, **kwargs):  # pragma: no cover - compatibility shim
        def wrapper(func):
            return func

        return wrapper

    backoff_stub.on_exception = _identity_decorator
    backoff_stub.expo = lambda *args, **kwargs: None
    sys.modules["backoff"] = backoff_stub

# Provide a stub for the openai client to avoid network calls during import.
if "openai" not in sys.modules:
    class _DummyCompletions:
        def create(self, **kwargs):  # pragma: no cover - import-time shim
            raise RuntimeError("OpenAI stub should be replaced in tests")

    class _DummyChat:
        def __init__(self):
            self.completions = _DummyCompletions()

    class _DummyOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = _DummyChat()

    openai_stub = types.SimpleNamespace(
        OpenAI=_DummyOpenAI,
        RateLimitError=Exception,
        APITimeoutError=Exception,
    )
    sys.modules["openai"] = openai_stub

# Provide a minimal requests stub to satisfy imports when the library is absent.
if "requests" not in sys.modules:
    class _HTTPError(Exception):
        def __init__(self, *args, **kwargs):
            super().__init__(*args)

    class _RequestsStub(types.SimpleNamespace):
        def __init__(self):
            super().__init__(exceptions=types.SimpleNamespace(HTTPError=_HTTPError))

        def get(self, *args, **kwargs):  # pragma: no cover - import-time shim
            raise RuntimeError("Requests stub should be patched in tests")

    sys.modules["requests"] = _RequestsStub()
