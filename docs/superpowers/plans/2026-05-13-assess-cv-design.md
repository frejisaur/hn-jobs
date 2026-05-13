# CV-to-Job Matching Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a `/assess-cv` command that scores a candidate's CV against all extracted HN jobs and writes ranked match results.

**Architecture:** Two Claude Code files — a command (`.claude/commands/assess-cv.md`) orchestrates file I/O and invokes a skill (`.claude/skills/assess-cv.md`) that defines the LLM scoring schema and instructions. No Python code — the entire flow is LLM-driven. Output goes to `data/matches/<candidate-slug>.jsonl`.

**Tech Stack:** Claude Code commands/skills (Markdown), JSONL data format

---

## File Structure

| File | Action | Responsibility |
|-|-|-|
| `.claude/skills/assess-cv.md` | Create | Scoring skill — defines dimensions, schema, calibration rules |
| `.claude/commands/assess-cv.md` | Create | Orchestration command — file I/O, slug derivation, skill invocation, summary output |
| `data/matches/` | Create directory | Output location for match JSONL files |
| `.claude/CLAUDE.md` | Modify | Document new command/skill in Extending section |

Dependencies: The skill must exist before the command references it. CLAUDE.md update comes last.

---

### Task 1: Create the scoring skill

**Files:**
- Create: `.claude/skills/assess-cv.md`

This is the reasoning core — defines what the LLM scores, how it calibrates, and the exact output schema. The command will reference this skill by name.

- [ ] **Step 1: Create `.claude/skills/assess-cv.md`**

```markdown
---
name: assess-cv
description: Score a candidate's CV against a batch of jobs. Returns a JSON array of scored match objects.
---

# Assess CV Against Jobs

You are a CV-to-job matching agent. You receive a candidate's CV and a set of job records, and you score every job against the CV.

## Input

You will receive:
- **CV text** -- full content of the candidate's CV file
- **Jobs array** -- all job records from `jobs.jsonl` (each is a `JobDescription` JSON object)
- **Candidate slug** -- identifier derived from the CV filename

## Scoring Dimensions

Score each job on four dimensions, each 0.0--1.0 with a one-line rationale:

| Dimension | What it measures |
|-|-|
| `skills` | Overlap between job's required skills/technologies and candidate's demonstrated skills/experience |
| `seniority` | Whether the candidate's experience level matches the job's YOE/seniority expectations |
| `domain` | Overlap between candidate's industry experience and the job's domain |
| `role_type` | Whether the candidate's career function aligns with the role (e.g., leadership vs. IC vs. GTM) |

## Overall Score

`overall_score` is your holistic judgment, not a mechanical average. Weigh dimensions contextually:
- Skills weight more for technical IC roles
- Seniority weighs more for leadership roles
- Domain weighs more for regulated industries (healthcare, insurance)

## Scoring Scale

| Range | Meaning |
|-|-|
| 0.8--1.0 | Strong match -- candidate could credibly apply |
| 0.6--0.79 | Moderate match -- relevant experience but notable gaps |
| 0.3--0.59 | Weak match -- some transferable elements, significant misalignment |
| 0.0--0.29 | No meaningful match -- different domain/function/level |

## Rules

1. **Rationales must cite evidence.** Reference specific skills, roles, or experience from both the CV and the job. Never write generic statements like "good fit" or "some overlap".
2. **Do not inflate scores.** A hardware executive with no software skills scores near 0 on a React/TypeScript IC role.
3. **Calibrate across jobs.** The best match should be meaningfully higher than the worst. Avoid score clustering -- if all scores land in 0.4--0.6, you're not differentiating.
4. **Return valid JSON array, no markdown fencing, no explanation.** Just the array.

## Output

Return a JSON array sorted by `overall_score` descending. Each element:

```json
{
  "item_id": "string -- HN item ID from the job record",
  "company": "string -- copied from job's company field",
  "title": "string -- copied from job's title field",
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
  "candidate": "string -- the candidate slug provided",
  "assessed_at": "string -- current ISO 8601 timestamp (e.g. 2026-05-13T14:30:00Z)"
}
```
```

- [ ] **Step 2: Verify the skill file is valid**

Run:
```bash
head -3 .claude/skills/assess-cv.md
```
Expected: the YAML frontmatter with `name: assess-cv`.

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/assess-cv.md
git commit -m "feat: add assess-cv scoring skill with dimension schema and calibration rules"
```

---

### Task 2: Create the orchestration command

**Files:**
- Create: `.claude/commands/assess-cv.md`

This command handles all file I/O, slug derivation, and invokes the skill. Follow the pattern from `.claude/commands/hn-jobs.md` — YAML frontmatter, clear flow steps, explicit error handling.

- [ ] **Step 1: Create `.claude/commands/assess-cv.md`**

```markdown
---
name: assess-cv
description: Assess a candidate's CV against extracted HN jobs and write ranked match results
---

# Assess CV Against Jobs

Score every extracted job against a candidate's CV using LLM-based confidence scoring.

## Arguments

This command receives a single argument: the path to the candidate's CV file (markdown).

If no argument is provided, stop and ask: "Usage: /assess-cv <path-to-cv.md>"

## Flow

### Step 1: Read the CV

Read the file at the provided path. If the file does not exist or is empty, stop and report the error.

### Step 2: Read all jobs

Read `data/jobs.jsonl`. Parse each line as JSON into an array. If the file is empty or missing, stop and report: "No extracted jobs found. Run /hn-jobs first."

### Step 3: Derive candidate slug

Extract the filename from the path (strip directory). Then:
1. Remove the file extension (`.md`, `.txt`, etc.)
2. Remove a trailing `-cv` suffix if present

Examples:
- `john-ternus-cv.md` -> `john-ternus`
- `tim-cook-cv.md` -> `tim-cook`
- `resume.md` -> `resume`
- `/some/path/jane-doe-cv.md` -> `jane-doe`

### Step 4: Score all jobs

Using the `assess-cv` skill, score every job against the CV in a single pass. Provide:
- The full CV text
- The full jobs array
- The candidate slug

The skill returns a JSON array of scored match objects sorted by `overall_score` descending.

### Step 5: Write results

1. Create the directory `data/matches/` if it does not exist
2. Write results to `data/matches/<candidate-slug>.jsonl` — one JSON object per line, preserving the descending score order from the skill output
3. If the file already exists, overwrite it (re-assessment replaces prior results)

### Step 6: Print summary

Print a summary:

```
## CV Match Results: <candidate-slug>

Assessed <N> jobs against <cv-filename>

### Top 5 Matches

1. **<company>** — <title> (score: <overall_score>)
   <summary>
2. ...

Results written to data/matches/<candidate-slug>.jsonl
```

## Error Handling

- **CV file not found or empty:** Stop immediately with clear error message.
- **No jobs.jsonl:** Stop with message to run /hn-jobs first.
- **Skill returns invalid JSON:** Report the error, do not write partial results.
- **Write failure:** Report explicitly. Never silently drop results.
```

- [ ] **Step 2: Verify the command file is valid**

Run:
```bash
head -3 .claude/commands/assess-cv.md
```
Expected: the YAML frontmatter with `name: assess-cv`.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/assess-cv.md
git commit -m "feat: add /assess-cv orchestration command"
```

---

### Task 3: Create the matches output directory

**Files:**
- Create: `data/matches/.gitkeep`

Follow the pattern from `data/raw/.gitkeep` — keep an empty directory tracked so the output location exists in fresh clones.

- [ ] **Step 1: Create directory and gitkeep**

```bash
mkdir -p data/matches
touch data/matches/.gitkeep
```

- [ ] **Step 2: Commit**

```bash
git add data/matches/.gitkeep
git commit -m "feat: add data/matches/ directory for CV match output"
```

---

### Task 4: Update CLAUDE.md

**Files:**
- Modify: `.claude/CLAUDE.md`

Add documentation for the new command and skill so future contributors know they exist.

- [ ] **Step 1: Add to the Extending section of `.claude/CLAUDE.md`**

After the existing bullet for "New pipeline stage", add:

```markdown
- **CV matching:** `/assess-cv <path>` scores a CV against all jobs in `jobs.jsonl` using the `assess-cv` skill. Output goes to `data/matches/<candidate-slug>.jsonl`. The skill (`.claude/skills/assess-cv.md`) is the source of truth for scoring dimensions and schema.
```

The full Extending section should read:

```markdown
## Extending

- **New CLI command:** Add to `tools/cli.py` as a `@cli.command()`. Follow existing patterns (load state, do work, save state).
- **New extracted field:** Add to both `JobDescription` in `models.py` and the schema in `.claude/skills/extract-job.md`. Must stay in sync.
- **New data source:** Add a fetcher function in `tools/fetcher.py`, wire it into `fetch_job_content`'s resolution chain.
- **New pipeline stage:** Add state tracking in `tools/state.py`, a CLI command in `cli.py`, and update `.claude/commands/hn-jobs.md` flow.
- **CV matching:** `/assess-cv <path>` scores a CV against all jobs in `jobs.jsonl` using the `assess-cv` skill. Output goes to `data/matches/<candidate-slug>.jsonl`. The skill (`.claude/skills/assess-cv.md`) is the source of truth for scoring dimensions and schema.
```

- [ ] **Step 2: Verify the edit**

Run:
```bash
grep "CV matching" .claude/CLAUDE.md
```
Expected: the new bullet point appears.

- [ ] **Step 3: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs: document /assess-cv command and skill in CLAUDE.md"
```

---

### Task 5: Smoke test the full flow

This is a manual validation — run the command against one of the existing CVs to verify end-to-end behavior.

- [ ] **Step 1: Run `/assess-cv` against a test CV**

```
/assess-cv data/CV/john-ternus-cv.md
```

- [ ] **Step 2: Verify output file was created**

```bash
ls -la data/matches/john-ternus.jsonl
```
Expected: file exists with non-zero size.

- [ ] **Step 3: Verify output format**

```bash
head -1 data/matches/john-ternus.jsonl | python3 -m json.tool
```
Expected: valid JSON with all required fields (`item_id`, `company`, `title`, `overall_score`, `scores` with four dimensions, `summary`, `candidate`, `assessed_at`).

- [ ] **Step 4: Verify score calibration**

```bash
cat data/matches/john-ternus.jsonl | python3 -c "
import json, sys
scores = [json.loads(line)['overall_score'] for line in sys.stdin]
print(f'Score range: {min(scores):.2f} - {max(scores):.2f}')
print(f'Spread: {max(scores) - min(scores):.2f}')
print(f'Jobs scored: {len(scores)}')
assert max(scores) - min(scores) > 0.3, 'Score clustering detected — spread too narrow'
print('Calibration OK')
"
```
Expected: Spread > 0.3, confirming the LLM is differentiating between jobs rather than clustering scores.

- [ ] **Step 5: Spot-check rationales**

Read `data/matches/john-ternus.jsonl` and verify:
- The highest-scored job has rationales citing specific CV experience that matches the job
- The lowest-scored job has rationales citing specific mismatches
- No rationale uses generic language like "good fit" or "some overlap"

- [ ] **Step 6: Commit the test output (optional)**

If the output looks good and you want to keep it as reference data:
```bash
git add data/matches/john-ternus.jsonl
git commit -m "data: add john-ternus CV match results"
```
