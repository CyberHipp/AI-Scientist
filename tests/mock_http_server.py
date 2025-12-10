import contextlib
import gzip
import http.server
import io
import json
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class _MockHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, fixtures_root: Path, *args, **kwargs):
        self.fixtures_root = fixtures_root
        super().__init__(*args, directory=str(fixtures_root), **kwargs)

    def log_message(self, format, *args):  # pragma: no cover - silence noisy logs
        return

    def _send_json(self, payload, status=200, headers=None):
        headers = headers or {}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for key, value in headers.items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_paginated(self, query):
        page = int(query.get("page", [1])[0])
        page_file = self.fixtures_root / "web" / "api" / "paginated" / f"page-{page}.json"
        if not page_file.exists():
            self._send_json({"detail": "not found"}, status=404)
            return
        link_header_parts = []
        if page > 1:
            link_header_parts.append(f"</api/paginated?page={page - 1}>; rel=\"prev\"")
        if page < 3:
            link_header_parts.append(f"</api/paginated?page={page + 1}>; rel=\"next\"")
        headers = {}
        if link_header_parts:
            headers["Link"] = ", ".join(link_header_parts)
        payload = json.loads(page_file.read_text())
        self._send_json(payload, headers=headers)

    def _send_chunked(self, chunks):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        for chunk in chunks:
            data = chunk.encode("utf-8")
            self.wfile.write(f"{len(data):X}\r\n".encode("ascii"))
            self.wfile.write(data + b"\r\n")
        self.wfile.write(b"0\r\n\r\n")

    def _handle_etag(self):
        etag_value = '"demo-etag"'
        if self.headers.get("If-None-Match") == etag_value:
            self.send_response(304)
            self.send_header("ETag", etag_value)
            self.end_headers()
            return
        body = b"fresh content"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("ETag", etag_value)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_gzip(self):
        raw = b"compressed payload"
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as f:
            f.write(raw)
        payload = buf.getvalue()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Encoding", "gzip")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _handle_brotli(self):
        # Provide a body plus Content-Encoding without depending on brotli packages.
        body = b"brotli-like payload"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Encoding", "br")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_invalid_json(self, partial=False):
        snippet = b'{"status": "partial"' if partial else b'{"status": invalid}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(snippet)

    def _handle_charset(self):
        body = "Café résumé".encode("iso-8859-1")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=iso-8859-1")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_edge(self, path, query):
        if path == "/edge/redirect-302":
            self.send_response(302)
            self.send_header("Location", "/site/article-1.html")
            self.end_headers()
            return
        if path.startswith("/edge/redirect-chain"):
            step = int(query.get("step", [1])[0])
            if step == 1:
                self.send_response(301)
                self.send_header("Location", "/edge/redirect-chain?step=2")
                self.end_headers()
            elif step == 2:
                self.send_response(302)
                self.send_header("Location", "/site/article-2.html")
                self.end_headers()
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"redirect complete")
            return
        if path == "/edge/not-found":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"missing")
            return
        if path == "/edge/error-500":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"server error")
            return
        if path == "/edge/rate-limited":
            self.send_response(429)
            self.send_header("Retry-After", "2")
            self.send_header("X-RateLimit-Limit", "10")
            self.send_header("X-RateLimit-Remaining", "0")
            self.send_header("X-RateLimit-Reset", str(int(time.time()) + 2))
            self.end_headers()
            self.wfile.write(b"too many requests")
            return
        if path == "/edge/chunked":
            self._send_chunked(["chunk-one", "chunk-two"])
            return
        if path == "/edge/slow":
            delay = float(query.get("delay", [0.2])[0])
            time.sleep(delay)
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"slept {delay}".encode())
            return
        if path == "/edge/gzip":
            self._handle_gzip()
            return
        if path == "/edge/br":
            self._handle_brotli()
            return
        if path == "/edge/etag":
            self._handle_etag()
            return
        if path == "/edge/charset":
            self._handle_charset()
            return
        if path == "/edge/invalid-json":
            self._handle_invalid_json(partial=False)
            return
        if path == "/edge/partial-json":
            self._handle_invalid_json(partial=True)
            return
        if path.startswith("/api/paginated"):
            self._handle_paginated(query)
            return
        return False

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path.startswith("/edge") or parsed.path.startswith("/api/paginated"):
            handled = self._handle_edge(parsed.path, query)
            if handled is False:
                self.send_error(404)
            return
        # Simple rewrites so fixture URLs can be referred to without the leading /web prefix.
        if parsed.path.startswith("/site/"):
            self.path = "/web" + parsed.path
        elif parsed.path.startswith("/api/"):
            self.path = "/web" + parsed.path
        elif parsed.path.startswith("/rss/"):
            self.path = "/web" + parsed.path
        elif parsed.path == "/robots.txt":
            self.path = "/web/robots.txt"
        elif parsed.path == "/sitemap.xml":
            self.path = "/web/sitemap.xml"
        return super().do_GET()


def _handler_factory(fixtures_root: Path):
    return lambda *args, **kwargs: _MockHandler(fixtures_root, *args, **kwargs)


@contextlib.contextmanager
def serve_fixtures(fixtures_root: Path):
    handler = _handler_factory(Path(fixtures_root))
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://{httpd.server_address[0]}:{httpd.server_address[1]}"
    try:
        yield base_url
    finally:
        httpd.shutdown()
        thread.join()


__all__ = ["serve_fixtures"]
