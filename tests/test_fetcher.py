"""Tests for the job page fetcher."""
import pytest
from unittest.mock import MagicMock, patch
from tools.fetcher import fetch_page, fetch_hn_item, fetch_job_content, _request_with_backoff, InsufficientContentError

def _make_response(text: str, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from requests.exceptions import HTTPError
        resp.raise_for_status.side_effect = HTTPError(f"{status_code}")
    return resp

def test_fetch_page_extracts_text():
    session = MagicMock()
    html = "<html><body><p>" + "Hello world. " * 20 + "</p></body></html>"
    session.get.return_value = _make_response(html)
    result = fetch_page("https://example.com", session=session)
    assert "Hello world" in result
    assert len(result) >= 100

def test_fetch_page_short_content_returns_empty():
    session = MagicMock()
    session.get.return_value = _make_response("<html><body>Hi</body></html>")
    result = fetch_page("https://example.com", session=session)
    assert result == ""

def test_fetch_hn_item_toptext():
    from pathlib import Path
    fixture = (Path(__file__).parent / "fixtures" / "hn_item_page.html").read_text()
    session = MagicMock()
    session.get.return_value = _make_response(fixture)
    result = fetch_hn_item("33333333", session=session)
    assert "inline job posting" in result

def test_fetch_job_content_inline():
    with patch("tools.fetcher.fetch_hn_item", return_value="inline content") as mock:
        result = fetch_job_content(url=None, item_id="123")
        assert result == "inline content"
        mock.assert_called_once()

def test_fetch_job_content_external():
    with patch("tools.fetcher.fetch_page", return_value="page content") as mock:
        result = fetch_job_content(url="https://example.com", item_id="456")
        assert result == "page content"

def test_fetch_job_content_empty_raises_insufficient():
    with patch("tools.fetcher.fetch_page", return_value=""):
        with pytest.raises(InsufficientContentError, match="Needs agent-browser"):
            fetch_job_content(url="https://example.com", item_id="456")

def test_backoff_retries(monkeypatch):
    monkeypatch.setattr("tools.fetcher.time.sleep", lambda _: None)
    session = MagicMock()
    fail_resp = _make_response("", status_code=500)
    ok_resp = _make_response("<html><body>OK</body></html>")
    session.get.side_effect = [fail_resp, ok_resp]
    result = _request_with_backoff(session, "https://example.com", max_retries=3)
    assert result == ok_resp
