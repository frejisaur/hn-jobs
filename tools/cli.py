"""Click CLI for hn-jobs."""

from __future__ import annotations

import json
import sys
import time

import click

from models import JobListing
from tools.fetcher import InsufficientContentError, fetch_job_content
from tools.poller import poll_jobs
from tools.state import (
    append_job,
    get_failed_ids,
    get_needs_browser,
    get_new_ids,
    list_raw_ids,
    load_extracted_ids,
    load_jobs,
    load_state,
    mark_failed,
    mark_fetched,
    save_state,
    write_raw,
)


@click.group()
def cli() -> None:
    """HN Jobs poller CLI."""


@cli.command()
@click.option("--retry-only", is_flag=True, help="Only retry previously failed jobs.")
@click.option("--delay", default=1.0, type=float, help="Seconds between HN requests.")
def poll(retry_only: bool, delay: float) -> None:
    """Poll HN /jobs for new listings and fetch their content."""
    import requests

    state = load_state()
    session = requests.Session()

    # Determine which IDs to process
    failed_ids = get_failed_ids(state)
    new_ids: list[str] = []
    listings_by_id: dict[str, JobListing] = {}

    if not retry_only:
        try:
            listings = poll_jobs(session=session)
        except Exception as exc:
            click.echo(f"Error polling /jobs: {exc}", err=True)
            sys.exit(1)

        listings_by_id = {l.item_id: l for l in listings}
        new_ids = get_new_ids(state, [l.item_id for l in listings])
    else:
        click.echo("Retry-only mode: skipping new job discovery.")

    ids_to_fetch = list(dict.fromkeys(new_ids + failed_ids))  # dedupe, preserve order

    if not ids_to_fetch:
        click.echo("No new or failed jobs to fetch.")
        state["last_poll"] = _now_iso()
        save_state(state)
        return

    fetched_count = 0
    failed_count = 0

    for i, item_id in enumerate(ids_to_fetch):
        listing = listings_by_id.get(item_id)
        url = listing.url if listing else None

        try:
            content = fetch_job_content(
                url=url,
                item_id=item_id,
                session=session,
            )
            write_raw(item_id, content)
            mark_fetched(state, item_id, url=url)
            fetched_count += 1
        except InsufficientContentError as exc:
            mark_failed(state, item_id, "needs_browser", url=url)
            failed_count += 1
            click.echo(f"  Needs agent-browser: {item_id} ({url})", err=True)
        except Exception as exc:
            error_code = type(exc).__name__
            mark_failed(state, item_id, error_code, url=url)
            failed_count += 1
            click.echo(f"  Failed {item_id}: {exc}", err=True)

        # Rate limit between requests (skip after last)
        if i < len(ids_to_fetch) - 1:
            time.sleep(delay)

    state["last_poll"] = _now_iso()
    save_state(state)

    click.echo(
        f"Found {len(new_ids)} new jobs, retried {len(failed_ids)} failed. "
        f"{fetched_count} fetched, {failed_count} still failing."
    )


@cli.command("browser-fetch")
@click.option("--timeout", default=30, type=int, help="Seconds to wait for page load.")
def browser_fetch(timeout: int) -> None:
    """Fetch failed 'needs_browser' jobs via agent-browser."""
    import shutil
    import subprocess

    if not shutil.which("agent-browser"):
        click.echo("agent-browser not found in PATH. Install it first.", err=True)
        sys.exit(1)

    state = load_state()
    needs = get_needs_browser(state)

    if not needs:
        click.echo("No jobs need agent-browser fallback.")
        return

    click.echo(f"{len(needs)} job(s) need agent-browser fallback.")
    fetched = 0
    failed = 0

    for item_id, url in needs:
        if not url:
            click.echo(f"  Skip {item_id}: no URL stored in state", err=True)
            failed += 1
            continue

        click.echo(f"  Fetching {item_id} via agent-browser: {url}")
        try:
            # Navigate to the page
            subprocess.run(
                ["agent-browser", "open", url],
                capture_output=True, text=True, timeout=timeout, check=True,
            )
            # Wait for JS-rendered content
            subprocess.run(
                ["agent-browser", "wait", "--load", "networkidle"],
                capture_output=True, text=True, timeout=timeout, check=True,
            )
            # Extract page text
            result = subprocess.run(
                ["agent-browser", "get", "text", "body"],
                capture_output=True, text=True, timeout=timeout, check=True,
            )
            text = result.stdout.strip()

            if len(text) < 100:
                click.echo(f"    Still insufficient content ({len(text)} chars)", err=True)
                mark_failed(state, item_id, "browser_insufficient", url=url)
                failed += 1
                continue

            write_raw(item_id, text)
            mark_fetched(state, item_id, url=url)
            fetched += 1
            click.echo(f"    OK ({len(text)} chars)")

        except subprocess.TimeoutExpired:
            mark_failed(state, item_id, "browser_timeout", url=url)
            failed += 1
            click.echo(f"    Timeout", err=True)
        except subprocess.CalledProcessError as exc:
            mark_failed(state, item_id, "browser_error", url=url)
            failed += 1
            click.echo(f"    Error: {exc.stderr.strip()}", err=True)

    save_state(state)
    click.echo(f"Browser fetch complete: {fetched} fetched, {failed} failed.")


@cli.command()
def extract() -> None:
    """List unextracted jobs (raw files not yet in jobs.jsonl)."""
    raw_ids = list_raw_ids()
    extracted_ids = load_extracted_ids()
    unextracted = [iid for iid in raw_ids if iid not in extracted_ids]

    if not unextracted:
        click.echo("All raw files have been extracted.")
        return

    click.echo(f"{len(unextracted)} unextracted job(s):")
    for iid in sorted(unextracted):
        click.echo(f"  {iid}  data/raw/{iid}.txt")


@cli.command("list")
def list_jobs() -> None:
    """Pretty-print extracted jobs from jobs.jsonl."""
    jobs = load_jobs()
    if not jobs:
        click.echo("No extracted jobs yet.")
        return

    for job in jobs:
        company = job.get("company") or "Unknown"
        title = job.get("title", "Untitled")
        location = job.get("location") or "N/A"
        salary = job.get("salary") or ""
        skills = ", ".join(job.get("skills", []))

        click.echo(f"{company} — {title}")
        click.echo(f"  Location: {location}")
        if salary:
            click.echo(f"  Salary: {salary}")
        if skills:
            click.echo(f"  Skills: {skills}")
        click.echo(f"  Summary: {job.get('description_summary', '')}")
        click.echo()


@cli.command()
def status() -> None:
    """Print pipeline status counts."""
    state = load_state()
    seen = state.get("seen_ids", {})

    fetched = sum(1 for v in seen.values() if v.get("status") == "fetched")
    failed_entries = {
        iid: v for iid, v in seen.items() if v.get("status") == "failed"
    }

    extracted_ids = load_extracted_ids()

    click.echo(f"Fetched: {fetched}")
    click.echo(f"Failed:  {len(failed_entries)}")
    if failed_entries:
        # Group by error code
        by_error: dict[str, int] = {}
        for v in failed_entries.values():
            err = v.get("error", "unknown")
            by_error[err] = by_error.get(err, 0) + 1
        for err, count in sorted(by_error.items()):
            click.echo(f"  {err}: {count}")
    click.echo(f"Extracted: {len(extracted_ids)}")


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
