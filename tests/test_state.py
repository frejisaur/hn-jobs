"""Tests for state management."""
import json
import pytest
from pathlib import Path
from tools.state import (
    load_state, save_state, mark_fetched, mark_failed,
    get_new_ids, get_failed_ids, write_raw, read_raw,
    list_raw_ids, load_extracted_ids, append_job, load_jobs,
)

@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    import tools.state as state_mod
    monkeypatch.setattr(state_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(state_mod, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(state_mod, "JOBS_FILE", tmp_path / "jobs.jsonl")
    monkeypatch.setattr(state_mod, "RAW_DIR", tmp_path / "raw")
    return tmp_path

def test_load_default_state(data_dir):
    state = load_state()
    assert state == {"seen_ids": {}, "last_poll": None}

def test_save_load_roundtrip(data_dir):
    state = {"seen_ids": {"123": {"status": "fetched"}}, "last_poll": "2026-01-01T00:00:00Z"}
    save_state(state)
    loaded = load_state()
    assert loaded == state

def test_mark_fetched(data_dir):
    state = load_state()
    mark_fetched(state, "abc")
    assert state["seen_ids"]["abc"]["status"] == "fetched"
    assert "fetched_at" in state["seen_ids"]["abc"]

def test_mark_failed(data_dir):
    state = load_state()
    mark_failed(state, "xyz", "timeout")
    assert state["seen_ids"]["xyz"]["status"] == "failed"
    assert state["seen_ids"]["xyz"]["error"] == "timeout"

def test_get_new_ids(data_dir):
    state = {"seen_ids": {"a": {"status": "fetched"}}, "last_poll": None}
    assert get_new_ids(state, ["a", "b", "c"]) == ["b", "c"]

def test_get_failed_ids(data_dir):
    state = {"seen_ids": {
        "a": {"status": "fetched"},
        "b": {"status": "failed", "error": "timeout"},
        "c": {"status": "failed", "error": "404"},
    }, "last_poll": None}
    assert sorted(get_failed_ids(state)) == ["b", "c"]

def test_raw_files(data_dir):
    write_raw("item1", "some content")
    assert read_raw("item1") == "some content"
    assert read_raw("nonexistent") is None
    assert "item1" in list_raw_ids()

def test_jsonl_operations(data_dir):
    assert load_extracted_ids() == set()
    assert load_jobs() == []

    job = json.dumps({"item_id": "j1", "title": "Test"})
    append_job(job)
    assert load_extracted_ids() == {"j1"}

    jobs = load_jobs()
    assert len(jobs) == 1
    assert jobs[0]["item_id"] == "j1"
