#!/usr/bin/env bash
# generate-claude-demo.sh — scaffolds a demo project showing
# CLAUDE.md, commands, skills, agents, and how they compose
# (commands invoke agents/skills, skills invoke agents).
#
# Usage: ./generate-claude-demo.sh <project-name>
set -euo pipefail

PROJECT="${1:?Usage: $0 <project-name>}"

if [ -d "$PROJECT" ]; then
    echo "Error: Directory '$PROJECT' already exists." >&2
    exit 1
fi

echo "Creating Claude Code demo project: $PROJECT"
echo ""

# --- Directory structure ---
mkdir -p "$PROJECT"/{.claude/{commands,skills,agents},src,tests}

# ============================================================
# CLAUDE.md — loaded automatically at the start of every session
# ============================================================
cat > "$PROJECT/CLAUDE.md" << 'CLAUDE_EOF'
# taskr — Claude Code Demo

A CLI task manager that demonstrates commands, skills, and agents.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Demo

Once setup is done, try this inside Claude Code:

```
/project:plan build a personal website
```

This single command shows the full chain: **command → skill → agent**.

1. The `/project:plan` command tells Claude to break your goal into tasks
2. Claude loads the `task-workflow` skill for guidelines on using taskr
3. Claude runs `taskr add` for each task it creates
4. The skill dispatches the `task-reporter` agent for a summary

After the demo, run `taskr list` to see everything that was added.

## taskr CLI

```bash
taskr add "Buy groceries" --priority high
taskr list
taskr list --status pending
taskr complete <id>
```

## Stack

- Python 3.10+, argparse, pytest
- JSON file storage (`.taskr.json`)

## Architecture

```
src/
  cli.py    — entry point, argument parsing
  utils.py  — data layer (load/save tasks, ID generation)
```
CLAUDE_EOF

# ============================================================
# .claude/settings.json — permissions
# ============================================================
cat > "$PROJECT/.claude/settings.json" << 'SETTINGS_EOF'
{
  "permissions": {
    "allow": [
      "Bash(python *)",
      "Bash(pip install *)",
      "Bash(pytest *)",
      "Bash(git *)",
      "Bash(taskr *)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push *)"
    ]
  }
}
SETTINGS_EOF

# ============================================================
# Command: /project:plan
#
# Commands live in .claude/commands/ and become slash commands.
# The user triggers them explicitly with /project:<filename>.
# $ARGUMENTS captures anything typed after the command name.
#
# This command invokes a skill — it tells Claude to follow the
# task-workflow skill while breaking a goal into tasks.
# ============================================================
cat > "$PROJECT/.claude/commands/plan.md" << 'CMD_EOF'
Break down a goal into actionable tasks using the taskr CLI.

Follow the `task-workflow` skill guidelines.

Goal: $ARGUMENTS
CMD_EOF

# ============================================================
# Skill: task-workflow
#
# Skills live in .claude/skills/ with YAML frontmatter.
# Claude loads them automatically when the conversation matches
# the description — the user doesn't invoke them directly.
#
# NOTE: This skill dispatches the task-reporter agent after
# adding tasks. Skills can dispatch agents as part of their
# workflow — this lets you compose reasoning (skills) with
# autonomous work (agents).
# ============================================================
cat > "$PROJECT/.claude/skills/task-workflow.md" << 'SKILL_EOF'
---
name: task-workflow
description: Use when adding, organizing, or managing tasks with the taskr CLI
---

# Task Workflow

## Before Adding Tasks

Run `taskr list` to check what already exists. Don't add duplicates.

## Adding Tasks

- Break the goal into 3-5 concrete, actionable tasks
- Set priority based on dependency order and importance:
  - `high` — must be done first or is critical
  - `medium` — important but not blocking
  - `low` — nice to have
- Use `taskr add "<title>" --priority <level>` for each task

## After Adding Tasks

Dispatch the `task-reporter` agent to generate a summary of all tasks.
SKILL_EOF

# ============================================================
# Agent: task-reporter
#
# Agents live in .claude/agents/ with YAML frontmatter.
# They run as autonomous subagents — separate Claude instances
# with their own tool access. Use them to delegate work that
# requires reasoning but can run independently.
# ============================================================
cat > "$PROJECT/.claude/agents/task-reporter.md" << 'AGENT_EOF'
---
name: task-reporter
description: Generates a summary report of all taskr tasks
model: haiku
tools:
  - Bash
---

# Task Reporter Agent

Run `taskr list --status all` and summarize the results.

## Output Format

Report:
- Total tasks, how many pending, how many done
- List any high-priority pending tasks
- One-line overall status (e.g., "3 of 5 tasks complete — 2 high-priority items remaining")
AGENT_EOF

# ============================================================
# Python source files
# ============================================================
cat > "$PROJECT/src/__init__.py" << 'EOF'
"""taskr — a minimal CLI task manager."""
EOF

cat > "$PROJECT/src/cli.py" << 'EOF'
"""CLI entry point for taskr."""

import argparse
import sys

from .utils import load_tasks, save_tasks, generate_id


def add_task(title: str, priority: str) -> None:
    """Add a new task to the local store."""
    tasks = load_tasks()
    task = {
        "id": generate_id(),
        "title": title,
        "priority": priority,
        "status": "pending",
    }
    tasks.append(task)
    save_tasks(tasks)
    print(f"Added task {task['id']}: {title} [{priority}]")


def list_tasks(status_filter: str) -> None:
    """Print tasks, optionally filtered by status."""
    tasks = load_tasks()
    if status_filter != "all":
        tasks = [t for t in tasks if t["status"] == status_filter]

    if not tasks:
        print("No tasks found.")
        return

    for task in tasks:
        marker = "x" if task["status"] == "done" else " "
        print(f"  [{marker}] {task['id']}  {task['title']}  ({task['priority']})")


def complete_task(task_id: str) -> None:
    """Mark a task as done by its ID."""
    tasks = load_tasks()
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = "done"
            save_tasks(tasks)
            print(f"Completed: {task['title']}")
            return

    print(f"Error: No task found with ID '{task_id}'", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    """Parse arguments and dispatch to the appropriate handler."""
    parser = argparse.ArgumentParser(
        prog="taskr",
        description="A minimal CLI task manager.",
    )
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument("title", help="Task title")
    add_parser.add_argument(
        "--priority",
        choices=["low", "medium", "high"],
        default="medium",
        help="Task priority (default: medium)",
    )

    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument(
        "--status",
        choices=["pending", "done", "all"],
        default="all",
        help="Filter by status (default: all)",
    )

    complete_parser = subparsers.add_parser("complete", help="Mark a task as done")
    complete_parser.add_argument("task_id", help="Task ID to complete")

    args = parser.parse_args()

    if args.command == "add":
        add_task(args.title, args.priority)
    elif args.command == "list":
        list_tasks(args.status)
    elif args.command == "complete":
        complete_task(args.task_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
EOF

cat > "$PROJECT/src/utils.py" << 'EOF'
"""Data access layer for taskr — handles persistence and IDs."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

TASKS_FILE = Path(".taskr.json")


def load_tasks() -> list[dict]:
    """Load tasks from the local JSON file."""
    if not TASKS_FILE.exists():
        return []
    return json.loads(TASKS_FILE.read_text())


def save_tasks(tasks: list[dict]) -> None:
    """Write tasks to the local JSON file."""
    TASKS_FILE.write_text(json.dumps(tasks, indent=2) + "\n")


def generate_id() -> str:
    """Generate a short unique task ID."""
    return uuid.uuid4().hex[:8]
EOF

# ============================================================
# Tests
# ============================================================
touch "$PROJECT/tests/__init__.py"

cat > "$PROJECT/tests/test_utils.py" << 'EOF'
"""Tests for taskr utilities."""

from src.utils import load_tasks, save_tasks, generate_id


def test_generate_id_is_8_char_hex():
    task_id = generate_id()
    assert len(task_id) == 8
    assert all(c in "0123456789abcdef" for c in task_id)


def test_generate_id_no_collisions():
    ids = {generate_id() for _ in range(100)}
    assert len(ids) == 100


def test_save_and_load_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr("src.utils.TASKS_FILE", tmp_path / ".taskr.json")
    tasks = [{"id": "abc12345", "title": "Test", "priority": "high", "status": "pending"}]
    save_tasks(tasks)
    assert load_tasks() == tasks


def test_load_returns_empty_when_no_file(tmp_path, monkeypatch):
    monkeypatch.setattr("src.utils.TASKS_FILE", tmp_path / ".taskr.json")
    assert load_tasks() == []
EOF

# ============================================================
# pyproject.toml
# ============================================================
cat > "$PROJECT/pyproject.toml" << 'EOF'
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "taskr"
version = "0.1.0"
description = "A minimal CLI task manager (Claude Code demo)"
requires-python = ">=3.10"

[tool.setuptools]
packages = ["src"]

[project.scripts]
taskr = "src.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
EOF

# ============================================================
# .gitignore
# ============================================================
cat > "$PROJECT/.gitignore" << 'EOF'
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.taskr.json
.venv/
EOF

# ============================================================
# Git init
# ============================================================
git -C "$PROJECT" init -q
git -C "$PROJECT" add -A
git -C "$PROJECT" commit -q -m "Initial commit: taskr demo project"

# ============================================================
# Summary
# ============================================================
echo "Done! Project structure:"
echo ""
echo "  $PROJECT/"
echo "  ├── CLAUDE.md                        # project context + demo instructions"
echo "  ├── .claude/"
echo "  │   ├── settings.json                # tool permissions"
echo "  │   ├── commands/"
echo "  │   │   └── plan.md                  # /project:plan  (command → skill → agent)"
echo "  │   ├── skills/"
echo "  │   │   └── task-workflow.md          # auto-loaded task management guidelines"
echo "  │   └── agents/"
echo "  │       └── task-reporter.md          # summarizes tasks autonomously"
echo "  ├── src/cli.py + utils.py"
echo "  ├── tests/test_utils.py"
echo "  └── pyproject.toml"
echo ""
echo "To demo, run:  cd $PROJECT && cat CLAUDE.md"
