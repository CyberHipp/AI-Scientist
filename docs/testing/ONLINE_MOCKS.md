# Offline web fixture pack

This repository includes a deterministic set of synthetic web and API documents for tests that would otherwise reach the public internet.

## Layout
- `fixtures/web/site`: HTML pages plus a malformed variant and basic static assets.
- `fixtures/web/api`: JSON endpoints for article lookups and paginated results.
- `fixtures/web/rss`: RSS feed sample.
- `fixtures/web/edge`: Served dynamically by the mock server for redirects, errors, rate limits, chunked responses, slow responses, compression, and ETag/charset cases.
- `fixtures/papers`: Minimal paper-like pages and TEI/metadata to exercise ingestion pipelines.
- `fixtures_manifest.json`: File list with SHA256 checksums for reproducibility.

## Usage
1. Start the local server inside tests using `serve_fixtures`:
   ```python
   from pathlib import Path
   from tests.mock_http_server import serve_fixtures

   fixtures = Path(__file__).resolve().parent.parent / "fixtures"
   with serve_fixtures(fixtures) as base_url:
       response = http_get(f"{base_url}/site/index.html")
   ```
2. Point crawlers/scrapers/RAG ingestion to the `base_url` instead of the public internet.
3. Prefer adding new edge cases here instead of relying on live sites. Keep fixtures synthetic (no real user or copyrighted content).

## Edge behaviors available
- Redirects (single hop and chains)
- 404/500 errors
- Rate limiting headers (429 + Retry-After)
- Chunked transfer encoding
- Slow responses (tunable via query param)
- Gzip and `br` compression headers
- ETag + If-None-Match / 304
- Charset variations
- Invalid and partial JSON payloads
- Paginated API with RFC5988 `Link` headers

## Extending fixtures
- Add files under `fixtures/` and update `fixtures_manifest.json` using the checksum helper below.
- Expand `tests/mock_http_server.py` to route new edge paths.
- Add or update tests in `tests/` to cover any new behavior.

### Regenerate manifest
Run the helper to refresh hashes after changing fixtures:
```bash
python scripts/update_fixture_manifest.py
```
