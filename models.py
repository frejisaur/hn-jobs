from __future__ import annotations

from pydantic import BaseModel, Field


class JobListing(BaseModel):
    """Raw listing scraped from HN /jobs page."""

    item_id: str
    title: str
    url: str | None = None
    posted_at: str
    source: str | None = None


class JobDescription(BaseModel):
    """Structured data extracted by the extraction skill."""

    item_id: str
    title: str
    company: str | None = None
    yoe: str | None = None
    salary: str | None = None
    skills: list[str] = Field(default_factory=list)
    location: str | None = None
    description_summary: str
    source_url: str | None = None
    extracted_at: str
