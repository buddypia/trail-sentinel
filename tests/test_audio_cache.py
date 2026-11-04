"""Immutable cache headers for /audio/* (F5 preload support). No sockets.

Pre-generated voice fragments are content-stable, so successful /audio/*
responses are marked immutable and the idle preload survives across
sessions. Everything else keeps no-cache — including /audio/* 404s, so a
page loaded before generation never pins a missing file forever.
"""
from __future__ import annotations

import http.server
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server


def headers_for(path: str, code: int) -> dict[str, str]:
    """Run Handler.send_response + end_headers with the socket writes stubbed."""
    base_send = http.server.BaseHTTPRequestHandler.send_response
    base_end = http.server.BaseHTTPRequestHandler.end_headers
    http.server.BaseHTTPRequestHandler.send_response = lambda self, c, m=None: None  # noqa: E731
    http.server.BaseHTTPRequestHandler.end_headers = lambda self: None  # noqa: E731
    try:
        handler = server.Handler.__new__(server.Handler)
        handler.path = path
        sent: dict[str, str] = {}
        handler.send_header = lambda k, v: sent.setdefault(k, v)  # noqa: E731
        handler.send_response(code)
        handler.end_headers()
        return sent
    finally:
        http.server.BaseHTTPRequestHandler.send_response = base_send
        http.server.BaseHTTPRequestHandler.end_headers = base_end


class AudioCacheHeaderTest(unittest.TestCase):
    def test_audio_200_is_immutable(self):
        headers = headers_for("/audio/ko/b_snake.mp3", 200)
        self.assertEqual(
            headers.get("Cache-Control"),
            "public, max-age=31536000, immutable",
        )

    def test_audio_404_stays_revalidatable(self):
        headers = headers_for("/audio/ko/b_snake.mp3", 404)
        self.assertEqual(
            headers.get("Cache-Control"), "no-cache, must-revalidate"
        )

    def test_other_static_stays_revalidatable(self):
        for path in ("/app.js", "/index.html", "/videos/x.mp4", "/api/status"):
            with self.subTest(path=path):
                headers = headers_for(path, 200)
                self.assertEqual(
                    headers.get("Cache-Control"), "no-cache, must-revalidate"
                )


if __name__ == "__main__":
    unittest.main()
