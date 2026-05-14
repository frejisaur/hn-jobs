# hn-jobs

A Hacker News job pipeline that demonstrates **multi-skill agentic workflows** with Claude Code.

The project pairs a conventional Python CLI (HTTP, parsing, state management) with Claude Code skills that handle the reasoning-heavy work (extracting structured data from varied page formats, scoring CVs against jobs). Neither side does the other's job.

## What it does

```
poll  -->  fetch  -->  browser-fetch (fallback)  -->  extract  -->  list
```

| Stage | What happens |
|-|-|
| `poll` | Scrapes HN `/jobs` for new listings, fetches page content |
| `browser-fetch` | Re-fetches JS-heavy pages via headless browser |
| `extract` | Claude reads raw page text, outputs structured `JobDescription` JSON |
| `list` | Pretty-prints extracted jobs |
| `assess-cv` | Claude scores a candidate's CV against all extracted jobs |

Each stage is **idempotent** -- re-running skips already-completed items.

## Prerequisites

### Python (3.11+)

```bash
pip install -e ".[dev]"
```

### Claude Code

Install Claude Code and authenticate:

```bash
npm install -g @anthropic-ai/claude-code
claude login
```

### Superpowers plugin (Claude Code marketplace)

This project uses skills from the [Superpowers](https://github.com/anthropics/superpowers) Claude Code plugin for structured workflows (brainstorming, TDD, debugging, planning, parallel agents).

Install from the Claude Code marketplace:

```
/install-plugin superpowers
```

### agent-browser CLI (optional, for `browser-fetch`)

Some job pages require JavaScript rendering. The `browser-fetch` command uses `agent-browser` to fetch these.

```bash
npm install -g agent-browser
```

Without it, JS-heavy pages will be skipped with a `needs_browser` status.

## Usage

### Run the full pipeline

```bash
claude "/hn-jobs"
```

This invokes the `hn-jobs` slash command, which orchestrates the full poll-fetch-extract cycle in a single Claude session.

### Run individual stages

```bash
hn-jobs poll              # Discover and fetch new jobs
hn-jobs browser-fetch     # Retry JS-heavy pages with headless browser
hn-jobs extract           # List unextracted jobs (extraction itself is done by Claude)
hn-jobs list              # Print all extracted jobs
hn-jobs status            # Pipeline status counts
```

### Assess a CV against jobs

```bash
claude "/assess-cv data/CV/tim-cook-cv.md"
```

Scores every extracted job against the candidate's CV and writes ranked results to `data/matches/<candidate-slug>.jsonl`.

## Project structure

```
.claude/
  CLAUDE.md              # Project instructions (architecture, constraints, extension guide)
  commands/
    hn-jobs.md            # /hn-jobs slash command -- orchestrates the full pipeline
    assess-cv.md          # /assess-cv slash command -- CV matching workflow
  skills/
    extract-job.md        # Extraction schema and rules (single source of truth)
    assess-cv.md          # CV scoring dimensions and output schema
  references/
    DESIGN.md             # Brand guidelines for UI work
  generate-claude-demo.sh # Standalone scaffolding script (see "Starter demo script")
tools/
  cli.py                  # Click CLI entry point
  poller.py               # HN /jobs HTML parser
  fetcher.py              # Page content fetcher (requests + BS4)
  state.py                # State and data persistence
models.py                 # Pydantic models: JobListing, JobDescription
data/
  state.json              # Pipeline state (seen IDs, statuses)
  raw/                    # Raw page text per job (one file per item ID)
  jobs.jsonl              # Extracted job records (append-only)
  matches/                # CV match results per candidate
  CV/                     # Sample CVs for testing
tests/                    # pytest suite for the Python tools
jobs.html                 # Static HTML view of extracted jobs
```

## Skills architecture

The project separates work by determinism:

- **Python CLI tools** handle predictable work: HTTP requests, HTML parsing, state management, file I/O.
- **Claude Code skills** handle reasoning work: extracting structured fields from varied page formats, scoring CVs against job requirements.

Skills live in `.claude/skills/` and define the schemas and rules. Commands in `.claude/commands/` orchestrate workflows that combine CLI tools with skill invocations.

## Next steps to build

### CV Assessor view

The `/assess-cv` command writes match results to JSONL, but there's no UI to view them. Build an HTML view (like `jobs.html`) that reads `data/matches/*.jsonl` and renders ranked match cards with score breakdowns.

### Generator-Critic assessment

The current CV scoring runs in a single pass. A stronger pattern would be:

1. **Generator** -- produces initial scores and rationales
2. **Critic** -- reviews scores for inflation, vague rationales, poor calibration across jobs
3. **Refinement** -- generator revises based on critic feedback
4. Repeat until the critic passes or a max iteration count is reached

This ensures scores are well-calibrated and rationales cite specific evidence. Rebuild the `assess-cv` skill using this pattern for production-grade accuracy.

## Starter demo script

The repo includes a standalone scaffolding script at `.claude/generate-claude-demo.sh` that generates a minimal Claude Code demo project (`taskr` — a CLI task manager) showing how commands, skills, and agents compose together.

Use it to quickly spin up a fresh project that demonstrates the `command -> skill -> agent` chain without any of the HN-specific plumbing.

```bash
# Copy the script OUT of this repo first — it creates a new directory
cp .claude/generate-claude-demo.sh ~/generate-claude-demo.sh

# Run it from a top-level directory (NOT inside .claude/)
cd ~
./generate-claude-demo.sh my-demo

# Then open the generated project in Claude Code
cd my-demo && claude
```

The generated project includes its own `CLAUDE.md` with demo instructions.

## Sample data

The repo includes sample data from a real pipeline run so you can explore the output without running the full pipeline:

- `data/raw/` -- raw page text for ~28 jobs
- `data/jobs.jsonl` -- extracted job records
- `data/CV/` -- sample CVs (Tim Cook, John Ternus) for testing CV matching
- `data/matches/tim-cook.jsonl` -- sample match results

## License

MIT
