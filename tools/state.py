"""State management for the HN jobs pipeline."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Default paths relative to project root
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = DATA_DIR / "state.json"
JOBS_FILE = DATA_DIR / "jobs.jsonl"
RAW_DIR = DATA_DIR / "raw"


def _ensure_dirs() -> None:
    """Create data directories if they don't exist."""
    DATA_DIR.mkdir(exist_ok=True)
    RAW_DIR.mkdir(exist_ok=True)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# state.json
# ---------------------------------------------------------------------------

def load_state() -> dict[str, Any]:
    """Load state.json, returning a default structure if it doesn't exist."""
    _ensure_dirs()
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"seen_ids": {}, "last_poll": None}


def save_state(state: dict[str, Any]) -> None:
    """Persist state to state.json."""
    _ensure_dirs()
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def mark_fetched(state: dict[str, Any], item_id: str, url: str | None = None) -> None:
    """Mark an item as successfully fetched."""
    entry: dict[str, Any] = {
        "status": "fetched",
        "fetched_at": _now_iso(),
    }
    if url is not None:
        entry["url"] = url
    state["seen_ids"][item_id] = entry


def mark_failed(state: dict[str, Any], item_id: str, error: str, url: str | None = None) -> None:
    """Mark an item as failed with an error code."""
    entry: dict[str, Any] = {
        "status": "failed",
        "error": error,
        "failed_at": _now_iso(),
    }
    if url is not None:
        entry["url"] = url
    state["seen_ids"][item_id] = entry


def get_new_ids(state: dict[str, Any], all_ids: list[str]) -> list[str]:
    """Return item IDs not yet seen in state."""
    seen = state.get("seen_ids", {})
    return [iid for iid in all_ids if iid not in seen]


def get_failed_ids(state: dict[str, Any]) -> list[str]:
    """Return item IDs with status 'failed'."""
    return [
        iid
        for iid, info in state.get("seen_ids", {}).items()
        if info.get("status") == "failed"
    ]


def get_needs_browser(state: dict[str, Any]) -> list[tuple[str, str | None]]:
    """Return (item_id, url) pairs for jobs that need agent-browser fallback."""
    return [
        (iid, info.get("url"))
        for iid, info in state.get("seen_ids", {}).items()
        if info.get("status") == "failed" and info.get("error") == "needs_browser"
    ]


# ---------------------------------------------------------------------------
# Raw files
# ---------------------------------------------------------------------------

def write_raw(item_id: str, content: str) -> Path:
    """Write raw page content to data/raw/<item_id>.txt."""
    _ensure_dirs()
    path = RAW_DIR / f"{item_id}.txt"
    path.write_text(content)
    return path


def read_raw(item_id: str) -> str | None:
    """Read raw page content, or None if not found."""
    path = RAW_DIR / f"{item_id}.txt"
    if path.exists():
        return path.read_text()
    return None


def list_raw_ids() -> list[str]:
    """Return item IDs that have raw files in data/raw/."""
    _ensure_dirs()
    return [p.stem for p in RAW_DIR.glob("*.txt")]


# ---------------------------------------------------------------------------
# jobs.jsonl
# ---------------------------------------------------------------------------

def load_extracted_ids() -> set[str]:
    """Return set of item IDs already in jobs.jsonl."""
    if not JOBS_FILE.exists():
        return set()
    ids: set[str] = set()
    for line in JOBS_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                ids.add(json.loads(line)["item_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    return ids


def append_job(job_json: str) -> None:
    """Append a single JobDescription JSON line to jobs.jsonl."""
    _ensure_dirs()
    with JOBS_FILE.open("a") as f:
        f.write(job_json.rstrip("\n") + "\n")


def load_jobs() -> list[dict[str, Any]]:
    """Load all jobs from jobs.jsonl."""
    if not JOBS_FILE.exists():
        return []
    jobs: list[dict[str, Any]] = []
    for line in JOBS_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                jobs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return jobs
