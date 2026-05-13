# hn-jobs

HN Jobs poller CLI — polls news.ycombinator.com/jobs, fetches page content, extracts structured job data.

## Architecture

Split by determinism: Python CLI tools handle predictable work (HTTP, parsing, state). Claude Code skills handle reasoning work (extracting structured fields from varied page formats). Never mix these — don't add LLM calls to Python tools or deterministic logic to skills.

**Pipeline:** `poll` → `fetch` → `browser-fetch` (fallback) → `extract` → `list`

Each stage is idempotent. State tracks which items reached which stage. Re-running any command skips already-completed items.

## Data Flow

| Stage | Input | Output | Storage |
|-|-|-|-|
| poll | HN /jobs HTML | `JobListing` objects | `state.json` (seen_ids) |
| fetch | Job page URL | Raw page text | `data/raw/<id>.txt` |
| extract | Raw text file | `JobDescription` JSON | `data/jobs.jsonl` (append-only) |

**Models** (`models.py`): `JobListing` (raw HN metadata) → `JobDescription` (structured extraction output). These are the only two schemas. New features that need persistent data should add a model here, not ad-hoc dicts.

**State** (`tools/state.py`): `state.json` tracks `seen_ids` with status (`fetched`|`failed`) and error codes. `jobs.jsonl` is append-only extracted output. Never mutate existing JSONL lines — append new versions if reprocessing.

## Constraints

- `poller.py` parses HN's HTML with BS4 selectors (`tr.athing`, `span.titleline`). If HN changes markup, this breaks — fix the selectors, don't add a fallback parser.
- `fetcher.py` raises `InsufficientContentError` when BS4 extraction returns <100 chars. The CLI catches this and marks `needs_browser` in state for the `browser-fetch` command.
- The `extract-job` skill (`.claude/skills/extract-job.md`) defines the extraction schema. Keep it as the single source of truth for `JobDescription` field semantics.

## Extending

- **New CLI command:** Add to `tools/cli.py` as a `@cli.command()`. Follow existing patterns (load state, do work, save state).
- **New extracted field:** Add to both `JobDescription` in `models.py` and the schema in `.claude/skills/extract-job.md`. Must stay in sync.
- **New data source:** Add a fetcher function in `tools/fetcher.py`, wire it into `fetch_job_content`'s resolution chain.
- **New pipeline stage:** Add state tracking in `tools/state.py`, a CLI command in `cli.py`, and update `.claude/commands/hn-jobs.md` flow.
- **CV matching:** `/assess-cv <path>` scores a CV against all jobs in `jobs.jsonl` using the `assess-cv` skill. Output goes to `data/matches/<candidate-slug>.jsonl`. The skill (`.claude/skills/assess-cv.md`) is the source of truth for scoring dimensions and schema.
