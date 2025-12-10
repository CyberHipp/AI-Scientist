import gzip
import json
import time
from pathlib import Path
from urllib import error, request

from tests.mock_http_server import serve_fixtures

FIXTURES_ROOT = Path(__file__).resolve().parent.parent / "fixtures"


def test_static_site_and_api():
    with serve_fixtures(FIXTURES_ROOT) as base_url:
        with request.urlopen(f"{base_url}/site/index.html") as resp:
            body = resp.read().decode("utf-8")
        assert "Mock Newsroom" in body

        with request.urlopen(f"{base_url}/api/search.json") as resp:
            data = json.loads(resp.read())
        assert data["query"] == "offline testing"
        assert len(data["results"]) == 2


def test_rss_and_paper_pages():
    with serve_fixtures(FIXTURES_ROOT) as base_url:
        with request.urlopen(f"{base_url}/rss/feed.xml") as resp:
            feed = resp.read().decode("utf-8")
        assert "Mock Feed" in feed

        with request.urlopen(f"{base_url}/papers/arxiv_2501.00001.html") as resp:
            html = resp.read().decode("utf-8")
        assert "Agentic Evaluation Without Internet" in html

        with request.urlopen(f"{base_url}/papers/2501.00001/metadata.json") as resp:
            metadata = json.loads(resp.read())
        assert metadata["id"] == "2501.00001"


def test_redirects_and_errors():
    with serve_fixtures(FIXTURES_ROOT) as base_url:
        # urllib follows redirects; final URL should resolve to article-1
        with request.urlopen(f"{base_url}/edge/redirect-302") as resp:
            final_url = resp.geturl()
        assert final_url.endswith("/site/article-1.html")

        try:
            request.urlopen(f"{base_url}/edge/not-found")
        except error.HTTPError as exc:
            assert exc.code == 404
        else:  # pragma: no cover - safety net
            raise AssertionError("404 endpoint should raise HTTPError")


def test_rate_limit_headers():
    with serve_fixtures(FIXTURES_ROOT) as base_url:
        try:
            request.urlopen(f"{base_url}/edge/rate-limited")
        except error.HTTPError as exc:
            assert exc.code == 429
            assert exc.headers["Retry-After"] == "2"
            assert exc.headers["X-RateLimit-Limit"] == "10"
            assert exc.headers["X-RateLimit-Remaining"] == "0"
        else:  # pragma: no cover - safety net
            raise AssertionError("429 endpoint should raise HTTPError")


def test_chunked_response_and_pagination():
    with serve_fixtures(FIXTURES_ROOT) as base_url:
        with request.urlopen(f"{base_url}/edge/chunked") as resp:
            content = resp.read().decode("utf-8")
        assert "chunk-one" in content and "chunk-two" in content

        with request.urlopen(f"{base_url}/api/paginated?page=2") as resp:
            payload = json.loads(resp.read())
            link_header = resp.headers.get("Link")
        assert payload["page"] == 2
        assert "rel=\"next\"" in link_header
        assert "rel=\"prev\"" in link_header


def test_slow_and_compressed_paths():
    with serve_fixtures(FIXTURES_ROOT) as base_url:
        start = time.perf_counter()
        with request.urlopen(f"{base_url}/edge/slow?delay=0.2", timeout=2) as resp:
            body = resp.read().decode()
        elapsed = time.perf_counter() - start
        assert elapsed >= 0.2
        assert body.startswith("slept 0.2")

        with request.urlopen(f"{base_url}/edge/gzip") as resp:
            compressed = resp.read()
        assert resp.headers.get("Content-Encoding") == "gzip"
        assert gzip.decompress(compressed) == b"compressed payload"

        with request.urlopen(f"{base_url}/edge/br") as resp:
            br_body = resp.read()
        assert resp.headers.get("Content-Encoding") == "br"
        assert br_body.startswith(b"brotli")


def test_etag_and_charset_and_invalid_json():
    with serve_fixtures(FIXTURES_ROOT) as base_url:
        # ETag fresh response
        request_obj = request.Request(f"{base_url}/edge/etag")
        with request.urlopen(request_obj) as resp:
            etag = resp.headers.get("ETag")
            content = resp.read().decode()
        assert etag == '"demo-etag"'
        assert content == "fresh content"

        # Conditional fetch should return 304
        conditional = request.Request(f"{base_url}/edge/etag", headers={"If-None-Match": etag})
        try:
            request.urlopen(conditional)
        except error.HTTPError as exc:
            assert exc.code == 304
        else:  # pragma: no cover - safety net
            raise AssertionError("Conditional request should yield 304")

        # Charset
        with request.urlopen(f"{base_url}/edge/charset") as resp:
            charset_header = resp.headers.get_content_charset()
            body = resp.read().decode(charset_header)
        assert "Café" in body

        # Invalid JSON
        with request.urlopen(f"{base_url}/edge/invalid-json") as resp:
            raw_json = resp.read().decode()
        try:
            json.loads(raw_json)
        except json.JSONDecodeError:
            pass
        else:  # pragma: no cover - safety net
            raise AssertionError("Invalid JSON should fail to parse")

        # Partial JSON
        with request.urlopen(f"{base_url}/edge/partial-json") as resp:
            partial_json = resp.read().decode()
        try:
            json.loads(partial_json)
        except json.JSONDecodeError:
            pass
        else:  # pragma: no cover - safety net
            raise AssertionError("Partial JSON should fail to parse")
