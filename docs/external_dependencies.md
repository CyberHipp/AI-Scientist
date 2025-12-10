# External dependencies

The AI-Scientist pipeline integrates with several third-party services for language-model inference and literature search:

- **OpenAI API** via the `openai` Python client for GPT-4o-family chat completions during idea generation, experimentation orchestration, and write-up drafting.
- **Anthropic API** for Claude models when selected as the LLM backend.
- **DeepSeek API** through the OpenAI-compatible client when `deepseek-coder-v2-0724` is chosen.
- **OpenRouter API** (OpenAI-compatible) to access Meta Llama 3.1 models.
- **Semantic Scholar Graph API** for novelty checks and citation search; requests are authenticated with the `S2_API_KEY` environment variable.

Tests in `tests/` verify both mocked success paths and error handling around these integrations.
