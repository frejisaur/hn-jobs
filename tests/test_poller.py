"""Tests for the HN /jobs page poller."""
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from models import JobListing
from tools.poller import poll_jobs

FIXTURES = Path(__file__).parent / "fixtures"

def _mock_session(html_file: str, status_code: int = 200):
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = (FIXTURES / html_file).read_text()
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        from requests.exceptions import HTTPError
        resp.raise_for_status.side_effect = HTTPError(f"{status_code}")
    session.get.return_value = resp
    return session

def test_parse_listings():
    session = _mock_session("hn_jobs_page.html")
    listings = poll_jobs(session=session)
    assert len(listings) == 3

    assert listings[0].item_id == "11111111"
    assert listings[0].title == "Acme Corp (YC W24) Is Hiring Engineers"
    assert listings[0].url == "https://acme.example.com/jobs"
    assert listings[0].source == "acme.example.com"
    assert listings[0].posted_at == "2 hours ago"

    assert listings[1].item_id == "22222222"
    assert listings[1].url == "https://widget.example.com/careers"

    # Inline post
    assert listings[2].item_id == "33333333"
    assert listings[2].url is None
    assert listings[2].source is None

def test_empty_page_raises():
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.text = "<html><body></body></html>"
    resp.raise_for_status = MagicMock()
    session.get.return_value = resp
    with pytest.raises(ValueError, match="Failed to parse"):
        poll_jobs(session=session)

def test_http_error():
    session = _mock_session("hn_jobs_page.html", status_code=500)
    with pytest.raises(Exception):
        poll_jobs(session=session)
