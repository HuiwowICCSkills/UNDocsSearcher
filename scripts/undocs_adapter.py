#!/usr/bin/env python3
"""United Nations documents adapter for UNDocsSearcher."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlparse

from bs4 import BeautifulSoup
from skillkit import HTTP, RetrievalError, clean, pdf_pages, result

PROG = "undocs_search.py"
DESCRIPTION = "Search UNITE/ODS United Nations documents and fetch PDFs by symbol."
CACHE_DEFAULT = ".undocs-cache"
FETCH_TIMEOUT_DEFAULT = 300

SEARCH_URL = "https://search.un.org/api/search"
SYMBOL_URL = "https://documents.un.org/api/symbol/access"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/155.0.0.0 Safari/537.36"
)


def _headers() -> dict[str, str]:
    return {
        "User-Agent": UA,
        "Accept": "application/json, text/html, application/pdf;q=0.9, */*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def make_http(args: argparse.Namespace) -> HTTP:
    return HTTP(
        args.cache,
        offline=args.offline,
        ttl=args.cache_ttl,
        timeout=args.timeout,
        user_agent=UA,
    )


def add_search_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--collection",
        choices=("un", "ods"),
        default="un",
        help="UNITE website index (un) or ODS collection (ods)",
    )
    parser.add_argument("--limit", type=int, default=10, help="1..50 (default 10)")
    parser.add_argument("--offset", type=int, default=0, help=">= 0 (default 0)")


def add_fetch_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text-out", help="Write extracted page text here")
    parser.add_argument("--pdf-out", help="Write a PDF response here")
    parser.add_argument("--max-mb", type=int, default=250, help="Maximum response size in MiB")


def _symbol_url(symbol: str, language: str = "E") -> str:
    return SYMBOL_URL + "?" + urlencode({"s": symbol, "l": language})


def search(query: str, args: argparse.Namespace, http: HTTP) -> dict[str, Any]:
    if not query.strip():
        raise ValueError("A non-empty query is required")
    if not 1 <= args.limit <= 50:
        raise ValueError("limit must be 1..50")
    if args.offset < 0:
        raise ValueError("offset must be >= 0")
    page = args.offset // 10 + 1
    data, meta = http.json(
        SEARCH_URL,
        {
            "collection": args.collection,
            "q": query,
            "row": 10,
            "sort": "relevance",
            "currentPageNumber": page,
        },
        headers=_headers(),
    )
    docs = data.get("docs")
    if not isinstance(docs, list):
        raise RetrievalError(
            "UN API omitted docs even though a count was supplied; cannot infer zero results"
        )
    rows: list[dict[str, Any]] = []
    for doc in docs[args.offset % 10 : args.offset % 10 + args.limit]:
        url = doc.get("url")
        if not url and doc.get("symbol"):
            url = _symbol_url(str(doc["symbol"]))
        if not url:
            raise RetrievalError("UN result has no document URL or symbol")
        rows.append(
            result(
                doc.get("title") or doc.get("symbol"),
                url,
                "unite-search",
                clean(doc.get("highlightedText") or doc.get("body")),
                symbol=doc.get("symbol"),
                language=doc.get("language"),
                provider="UN Unite Search",
                collection=args.collection,
                content_scope=(
                    "UN website index snippet; may include news, not only legal documents"
                    if args.collection == "un"
                    else "ODS document metadata"
                ),
            )
        )
    total = data.get("numberDocsFound")
    return {
        "status": "fallback" if args.collection == "un" else "ok",
        "query": query,
        "collection": args.collection,
        "total": total,
        "results": rows,
        "pagination": {
            "offset": args.offset,
            "limit": args.limit,
            "next_offset": args.offset + len(rows)
            if isinstance(total, int) and rows and args.offset + len(rows) < total
            else None,
        },
        "scope": (
            "UN Unite Search collection="
            + args.collection
            + "; the 'un' collection includes website/news records; ODS keyword search may be incomplete"
        ),
        "evidence": http.evidence,
    }


def fetch(locator: str, args: argparse.Namespace, http: HTTP) -> dict[str, Any]:
    if locator.startswith("http://") or locator.startswith("https://"):
        parsed = urlparse(locator)
        if parsed.scheme != "https" or (parsed.hostname or "").lower() not in {
            "search.un.org",
            "documents.un.org",
        }:
            raise ValueError("fetch expects an https://search.un.org/ or https://documents.un.org/ URL")
        url = locator
    else:
        url = _symbol_url(locator.strip())
    max_bytes = args.max_mb * 1024 * 1024
    body, meta = http.get(url, headers=_headers())
    if len(body) > max_bytes:
        raise RetrievalError(f"Response exceeds --max-mb ({args.max_mb} MiB)")
    if body.startswith(b"%PDF"):
        pages = pdf_pages(body)
        text = "\n\n".join(f"@@PAGE {p['page']}@@\n{p['text']}" for p in pages)
        if args.pdf_out:
            Path(args.pdf_out).write_bytes(body)
        if args.text_out:
            Path(args.text_out).write_text(text, encoding="utf-8")
        return {
            "status": "ok",
            "url": meta["source_url"],
            "pages": len(pages),
            "needs_ocr": not any(p["text"].strip() for p in pages),
            "page_text": pages,
            "pdf_out": str(Path(args.pdf_out).resolve()) if args.pdf_out else None,
            "text_out": str(Path(args.text_out).resolve()) if args.text_out else None,
            "sha256": meta["sha256"],
            "retrieved_at": meta["retrieved_at"],
        }
    if "json" in meta["content_type"].lower():
        return {
            "status": "ok",
            "url": meta["source_url"],
            "data": json.loads(body),
            "sha256": meta["sha256"],
            "retrieved_at": meta["retrieved_at"],
        }
    soup = BeautifulSoup(body, "html.parser")
    container = soup.select_one("main") or soup.body or soup
    for node in container.select("script, style, nav, header, footer, input, select, button, textarea, noscript"):
        node.decompose()
    text = container.get_text("\n", strip=True)
    if len(text) < 100:
        raise RetrievalError("Insufficient UN document page text")
    if args.text_out:
        Path(args.text_out).write_text(text, encoding="utf-8")
    return {
        "status": "ok",
        "url": meta["source_url"],
        "text": text,
        "text_characters": len(text),
        "content_scope": "UN document HTML page text; linked PDFs must be fetched separately",
        "text_out": str(Path(args.text_out).resolve()) if args.text_out else None,
        "sha256": meta["sha256"],
        "retrieved_at": meta["retrieved_at"],
    }


def doctor(args: argparse.Namespace) -> dict[str, Any]:
    checks = [
        {"check": "python", "ok": True, "detail": "Python runtime available"},
        {"check": "requests", "ok": True, "detail": "requests importable"},
        {"check": "beautifulsoup4", "ok": True, "detail": "bs4 importable"},
    ]
    if args.no_probe:
        return {"ok": True, "status": "ok (probes skipped)", "checks": checks}
    http = make_http(args)
    probes = []
    for collection in ("un", "ods"):
        try:
            data, meta = http.json(
                SEARCH_URL,
                {
                    "collection": collection,
                    "q": "charter",
                    "row": 1,
                    "sort": "relevance",
                    "currentPageNumber": 1,
                },
                headers=_headers(),
            )
            probes.append(
                {
                    "check": "UNITE/" + collection,
                    "ok": isinstance(data.get("docs"), list),
                    "http_status": meta["http_status"],
                    "bytes": meta["bytes"],
                }
            )
        except Exception as exc:
            probes.append({"check": "UNITE/" + collection, "ok": False, "error": f"{type(exc).__name__}: {exc}"})
    checks.extend(probes)
    ok = any(item.get("ok") for item in probes)
    return {
        "ok": ok,
        "status": "ok" if ok else "error",
        "checks": checks,
        "catalog": {"search": SEARCH_URL, "symbol": SYMBOL_URL},
    }
