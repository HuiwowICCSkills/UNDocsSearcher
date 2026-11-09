"""Offline tests for UNDocsSearcher."""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import undocs_adapter as adapter  # noqa: E402


class FakeHttp:
    def __init__(self, data):
        self.data = data
        self.evidence = []

    def json(self, url, params=None, headers=None):
        return self.data, {"source_url": url, "http_status": 200, "content_type": "application/json",
                           "bytes": 100, "retrieved_at": "2026-11-09T00:00:00Z", "sha256": "0" * 64}


def args(**kwargs):
    base = dict(collection="un", limit=1, offset=0, cache=".cache", offline=False, cache_ttl=0, timeout=30)
    base.update(kwargs)
    return argparse.Namespace(**base)


class UndocsTests(unittest.TestCase):
    def test_search_builds_symbol_url(self):
        payload = {"numberDocsFound": 1, "docs": [{"title": "Charter", "symbol": "A/RES/70/1"}]}
        out = adapter.search("charter", args(), FakeHttp(payload))
        self.assertEqual(out["status"], "fallback")
        self.assertEqual(out["total"], 1)
        self.assertIn("documents.un.org/api/symbol/access", out["results"][0]["url"])


if __name__ == "__main__":
    unittest.main()
