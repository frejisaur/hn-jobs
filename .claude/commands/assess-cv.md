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
