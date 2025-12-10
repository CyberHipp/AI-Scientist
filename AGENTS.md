# Agent Guidelines for This Repository

## Scope
These instructions apply to the entire repository. Add more specific AGENTS.md files in subdirectories if narrower rules are required.

## Coding conventions
- Favor clear, small functions with explicit inputs/outputs; keep side effects confined to orchestrator entry points.
- Preserve the existing offline-friendly behavior (mock dependency paths, no silent network calls). When adding new integrations, provide a mock/offline path.
- Avoid introducing new required services or environment variables without documenting them in `docs/`.
- Keep changes backward-compatible for CLI flags and config files whenever possible; if you add a new flag or setting, update the relevant docs and defaults.

## Testing and validation
- Update the test suite to reflect your changes; do not leave stale expectations or untested branches. Every behavior change should have a corresponding test update or addition.
- Run `pytest -q` after making changes to verify the baseline suite. Add targeted tests when touching orchestration, dependency handling, or experiment runners.
- For CLI changes, at least run `python launch_scientist.py --help` to ensure the argument parser remains healthy.

## Documentation
- Update or add markdown files in `docs/` when altering architecture, configuration, or workflow expectations. Keep docs concise and actionable.

## Workflow hygiene
- Read `CHANGELOG.md` before starting work to understand recent changes and expectations.
- Append a new entry to `CHANGELOG.md` that summarizes your changes before opening a pull request.
- If you are unsure whether your branch is merged, follow `docs/merge_verification.md` to confirm status before proceeding.

## Security & safety
- Do not hard-code secrets or enable outbound network calls in worker paths. Maintain sandbox-friendly patterns.
