"""HN /jobs page poller. Fetches and parses job listings."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from models import JobListing


def poll_jobs(session: requests.Session | None = None) -> list[JobListing]:
    """Fetch https://news.ycombinator.com/jobs and return parsed JobListing objects."""
    if session is None:
        session = requests.Session()

    resp = session.get("https://news.ycombinator.com/jobs")
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    listings: list[JobListing] = []

    for athing in soup.select("tr.athing"):
        item_id = athing.get("id")
        if not item_id:
            continue

        titleline = athing.select_one("td.title span.titleline")
        if not titleline:
            continue

        link = titleline.select_one("a")
        if not link:
            continue

        title = link.get_text(strip=True)
        href = link.get("href", "")

        # Inline HN posts link to item?id=X — no external URL
        if href.startswith("item?id="):
            url = None
            source = None
        else:
            url = href or None
            sitestr = titleline.select_one("span.sitestr")
            source = sitestr.get_text(strip=True) if sitestr else None

        # Age is in the next sibling <tr>, inside <span class="age">
        subtext_row = athing.find_next_sibling("tr")
        age_span = subtext_row.select_one("span.age") if subtext_row else None
        posted_at = age_span.get_text(strip=True) if age_span else ""

        listings.append(
            JobListing(
                item_id=item_id,
                title=title,
                url=url,
                posted_at=posted_at,
                source=source,
            )
        )

    if not listings:
        raise ValueError(
            "Failed to parse /jobs page — expected format may have changed"
        )

    return listings
