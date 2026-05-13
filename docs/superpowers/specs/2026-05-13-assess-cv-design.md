# CV-to-Job Matching Skill

Assess a candidate's CV against extracted HN jobs using LLM-based confidence scoring.

## Overview

A custom command (`/assess-cv`) reads a candidate's CV and all extracted jobs from `jobs.jsonl`, scores every job against the CV using an LLM skill, and writes ranked results to `data/matches/<candidate-slug>.jsonl`. The UI in `jobs.html` will consume this data to add a "CV Match" tab.

## Architecture

Follows the project's determinism split: the custom command handles orchestration (file I/O, slug derivation), the skill handles reasoning (scoring). No Python CLI involvement -- the entire flow is LLM-driven via two files:

- `.claude/commands/assess-cv.md` -- orchestration command
- `.claude/skills/assess-cv.md` -- scoring skill (schema + instructions)

### Approach: Single-Pass Scoring

All jobs are fed to the LLM alongside the CV in a single prompt. This allows the LLM to calibrate scores relative to each other -- if job A is a 0.8, job B should be meaningfully different at 0.3, not clustered at 0.6. The current dataset (~29 jobs) fits comfortably in context. If job count grows significantly, batching into groups of ~20 can be added later.

## Command: `/assess-cv`

Invoked as `/assess-cv <path-to-cv>`.

### Flow

1. Read the CV file at the provided path
2. Read all jobs from `data/jobs.jsonl`
3. Derive candidate slug from filename (`john-ternus-cv.md` -> `john-ternus`)
4. Score every job against the CV using the `assess-cv` skill in a single pass
5. Write results to `data/matches/<candidate-slug>.jsonl` (one JSON line per job, sorted by `overall_score` descending)
6. Print summary: top 5 matches with scores, total jobs assessed

### Slug Derivation

Strip the file extension and any trailing `-cv` suffix from the filename:
- `john-ternus-cv.md` -> `john-ternus`
- `tim-cook-cv.md` -> `tim-cook`
- `resume.md` -> `resume`

## Scoring Skill: `assess-cv`

### Input

The skill receives:
- **CV text** -- full content of the candidate's CV file
- **Jobs array** -- all job records from `jobs.jsonl`

### Scoring Dimensions

Each job is scored on four dimensions, each 0.0--1.0 with a one-line rationale:

| Dimension | What it measures |
|-|-|
| `skills` | Overlap between job's required skills/technologies and candidate's demonstrated skills/experience |
| `seniority` | Whether the candidate's experience level matches the job's YOE/seniority expectations |
| `domain` | Overlap between candidate's industry experience and the job's domain |
| `role_type` | Whether the candidate's career function aligns with the role (e.g., leadership vs. IC vs. GTM) |

### Overall Score

`overall_score` is the LLM's holistic judgment, not a mechanical average. The LLM weighs dimensions contextually:
- Skills weight more for technical IC roles
- Seniority weighs more for leadership roles
- Domain weighs more for regulated industries (healthcare, insurance)

### Scoring Scale

| Range | Meaning |
|-|-|
| 0.8--1.0 | Strong match -- candidate could credibly apply |
| 0.6--0.79 | Moderate match -- relevant experience but notable gaps |
| 0.3--0.59 | Weak match -- some transferable elements, significant misalignment |
| 0.0--0.29 | No meaningful match -- different domain/function/level |

### Scoring Rules

- Rationales must reference specific evidence from both the CV and job, not generic statements
- Do not inflate scores -- a hardware executive with no software skills scores near 0 on a React/TypeScript IC role
- Calibrate across jobs -- the best match should be meaningfully higher than the worst; avoid score clustering
- Return valid JSON array, no markdown fencing

## Output Schema

Each line in `data/matches/<candidate-slug>.jsonl`:

```json
{
  "item_id": "47777902",
  "company": "Proliferate",
  "title": "Founding Engineer",
  "overall_score": 0.15,
  "scores": {
    "skills": {
      "score": 0.1,
      "rationale": "Job requires TypeScript/React/Rust; candidate background is mechanical engineering and hardware architecture"
    },
    "seniority": {
      "score": 0.3,
      "rationale": "SVP-level executive applying for IC founding role; massively overqualified"
    },
    "domain": {
      "score": 0.1,
      "rationale": "Hardware product development vs. developer tooling SaaS; no overlap"
    },
    "role_type": {
      "score": 0.2,
      "rationale": "Engineering leadership transferable, but role expects hands-on coding"
    }
  },
  "summary": "Significant mismatch -- hardware executive profile vs. early-stage software IC role",
  "candidate": "john-ternus",
  "assessed_at": "2026-05-13T14:30:00Z"
}
```

### Field Descriptions

| Field | Type | Description |
|-|-|-|
| `item_id` | string | HN item ID, links to the job in `jobs.jsonl` |
| `company` | string | Copied from job for UI convenience |
| `title` | string | Copied from job for UI convenience |
| `overall_score` | float | 0.0--1.0 holistic match score |
| `scores` | object | Four dimension scores with rationales |
| `summary` | string | One-sentence match/mismatch explanation |
| `candidate` | string | Slug derived from CV filename |
| `assessed_at` | string | ISO 8601 timestamp of assessment |

## UI Integration (follow-on task)

Not part of this skill implementation, but documents the intended consumption:

- `jobs.html` gets a "CV Match" tab in the filter pills
- Match data embedded as `const MATCHES = [...]` alongside existing `JOBS` array
- When active: job cards show color-coded score badges, re-sort by `overall_score`, and display dimension scores in an expandable section
- The `summary` field appears below the existing job description summary
- A separate command or manual step regenerates `jobs.html` with match data

## File Changes

| File | Action |
|-|-|
| `.claude/commands/assess-cv.md` | Create -- orchestration command |
| `.claude/skills/assess-cv.md` | Create -- scoring skill with schema and instructions |
| `data/matches/` | Create directory -- output location for match JSONL files |
| `.claude/CLAUDE.md` | Update -- document new command and skill in Extending section |

## Out of Scope

- Python CLI command (no deterministic work to justify it)
- Batch CV processing (one CV at a time via explicit path)
- UI implementation in `jobs.html` (separate follow-on task)
- PDF CV parsing (only `.md` CVs supported; PDF support can be added later)
