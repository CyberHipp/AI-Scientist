# External dependencies

The AI-Scientist pipeline integrates with several third-party services for language-model inference and literature search. Set the noted environment variables before running the pipeline so the SDKs can authenticate correctly:

- **OpenAI API** via the `openai` Python client for GPT-4o-family chat completions during idea generation, experimentation orchestration, and write-up drafting. Requires `OPENAI_API_KEY`.
- **Anthropic API** for Claude models when selected as the LLM backend. Requires `ANTHROPIC_API_KEY` and the `anthropic` Python package.
- **DeepSeek API** through the OpenAI-compatible client when `deepseek-coder-v2-0724` is chosen. Requires `DEEPSEEK_API_KEY` and sets `base_url="https://api.deepseek.com"`.
- **OpenRouter API** (OpenAI-compatible) to access Meta Llama 3.1 models. Requires `OPENROUTER_API_KEY`.
- **Semantic Scholar Graph API** for novelty checks and citation search; requests are authenticated with the `S2_API_KEY` environment variable.

Tests in `tests/` verify both mocked success paths and error handling around these integrations, including missing API-key scenarios.

## Offline mock mode

Pass `--mock-dependencies` (or set `MOCK_DEPENDENCIES=1`) to run the pipeline without importing external SDKs or making network calls. This mock path injects deterministic LLM responses and Semantic Scholar results so you can exercise the control flow in constrained environments.
