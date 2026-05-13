"""Tests for CLI commands."""
import json
import pytest
from click.testing import CliRunner
from tools.cli import cli

@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    import tools.state as state_mod
    monkeypatch.setattr(state_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(state_mod, "STATE_FILE", tmp_path / "state.json")
    monkeypatch.setattr(state_mod, "JOBS_FILE", tmp_path / "jobs.jsonl")
    monkeypatch.setattr(state_mod, "RAW_DIR", tmp_path / "raw")
    (tmp_path / "raw").mkdir()
    return tmp_path

def test_status_empty(data_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Fetched: 0" in result.output

def test_extract_none(data_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["extract"])
    assert result.exit_code == 0
    assert "All raw files have been extracted" in result.output

def test_extract_shows_unextracted(data_dir):
    (data_dir / "raw" / "99999.txt").write_text("raw content")
    runner = CliRunner()
    result = runner.invoke(cli, ["extract"])
    assert "99999" in result.output

def test_list_empty(data_dir):
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No extracted jobs" in result.output

def test_list_with_jobs(data_dir):
    job = {"item_id": "1", "title": "Engineer", "company": "Acme", "location": "Remote", "skills": ["Python"], "description_summary": "A role.", "salary": "$100k", "extracted_at": "2026-01-01T00:00:00Z"}
    (data_dir / "jobs.jsonl").write_text(json.dumps(job) + "\n")
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert "Acme" in result.output
    assert "Engineer" in result.output
    assert "Remote" in result.output
