"""Job page fetcher. HTTP fetch with fallback chain."""

from __future__ import annotations

import logging
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (compatible; hn-jobs-bot/1.0; "
    "+https://github.com/hn-jobs)"
)

STRIP_TAGS = {"nav", "header", "footer", "script", "style", "noscript"}


def _request_with_backoff(
    session: requests.Session,
    url: str,
    max_retries: int = 3,
) -> requests.Response:
    """GET *url* with exponential backoff on 429 / 5xx errors."""
    delay = 1
    for attempt in range(max_retries):
        resp = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt == max_retries - 1:
                resp.raise_for_status()
            logger.warning(
                "HTTP %s from %s — retrying in %ss (attempt %d/%d)",
                resp.status_code,
                url,
                delay,
                attempt + 1,
                max_retries,
            )
            time.sleep(delay)
            delay *= 2
            continue
        resp.raise_for_status()
        return resp
    # Should not be reached, but satisfy type-checkers.
    raise RuntimeError("Exhausted retries")  # pragma: no cover


def fetch_page(
    url: str,
    session: requests.Session | None = None,
) -> str:
    """Fetch *url* and return meaningful text content.

    Returns an empty string when the extracted text is < 100 characters,
    signalling the caller to try a fallback strategy.
    """
    if session is None:
        session = requests.Session()

    resp = _request_with_backoff(session, url)
    soup = BeautifulSoup(resp.text, "html.parser")

    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    if len(text) < 100:
        logger.info("Page text too short (%d chars) for %s", len(text), url)
        return ""

    return text


def fetch_hn_item(
    item_id: str,
    session: requests.Session | None = None,
) -> str:
    """Fetch an HN item page and return its post / comment text."""
    if session is None:
        session = requests.Session()

    url = f"https://news.ycombinator.com/item?id={item_id}"
    resp = _request_with_backoff(session, url)
    soup = BeautifulSoup(resp.text, "html.parser")

    # "Ask HN" style posts keep the body in <div class="toptext">
    toptext = soup.select_one("div.toptext")
    if toptext:
        return toptext.get_text(separator="\n", strip=True)

    # Regular comment / post text lives in <td class="comment">
    comment = soup.select_one("td.comment")
    if comment:
        return comment.get_text(separator="\n", strip=True)

    # Fallback: strip boilerplate and return whatever remains.
    for tag in soup.find_all(STRIP_TAGS):
        tag.decompose()

    return soup.get_text(separator="\n", strip=True)


class InsufficientContentError(ValueError):
    """Raised when HTTP+BS4 extraction returns <100 chars of content.

    The orchestrator should catch this and dispatch a subagent with
    agent-browser to fetch the page instead.
    """


def fetch_job_content(
    url: str | None,
    item_id: str,
    session: requests.Session | None = None,
) -> str:
    """Return the raw text content for a job posting.

    Resolution order:
    1. If *url* is None (inline post) -> fetch_hn_item.
    2. fetch_page(url) via HTTP + BeautifulSoup.
    3. Raise InsufficientContentError so the orchestrator can dispatch
       a subagent with agent-browser as fallback.
    """
    if session is None:
        session = requests.Session()

    # Inline HN post — no external URL.
    if url is None:
        return fetch_hn_item(item_id, session=session)

    # Try a plain HTTP fetch.
    text = fetch_page(url, session=session)
    if text:
        return text

    raise InsufficientContentError(
        f"HTTP+BS4 returned <100 chars for {url} (item {item_id}). "
        f"Needs agent-browser fallback."
    )
