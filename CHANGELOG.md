# Changelog

All notable changes to this project are documented in this file. Add entries under the most recent heading when you land meaningful changes.

## Unreleased

### Added
- Repository-wide agent guidelines for coding style, testing, documentation, and safety expectations. [Scope: entire repo.]
- Reinforced agent testing instructions: update tests alongside code changes and keep `pytest -q` passing before pull requests.
- Offline/mock dependency workflows that keep idea generation and orchestration usable without external API clients, including CLI support for dependency-aware runs.
- MAS v1→v2 architecture blueprint describing Ollama-backed LLM evaluation pipelines with VM workers, curated mirrors, and governance for internal datasets.
- External dependency overview with required environment variables and API key expectations.
- Tests that validate mocked external dependency behavior and error reporting when APIs or credentials are missing.
- Run-attempt logging for offline execution of a user-requested paper-generation task.
- Repository workflow guidance that requires reading and updating `CHANGELOG.md` before opening pull requests.
- Merge verification checklist documenting how to confirm whether local commits are merged or pending before starting new work.

### Changed
- Template idea cache for `nanoGPT_lite` trimmed to reflect novel idea generation with mock dependencies.

### Notes
- Keep new features backward-compatible; prefer offline-friendly defaults and document new flags or settings in `docs/`.
