# Design: jobs.html Redesign

## Goal

Redesign `jobs.html` to match the Architectural Schematic brand guidelines (`.claude/references/DESIGN.md`) and improve information density with a two-panel layout and prominent apply button.

## Layout

### Desktop (>=768px)

Fixed split panel, full viewport height (`100vh`), no page-level scroll.

- **List panel (left):** 380px fixed width. Contains header, search, filters, and scrollable job list.
- **Detail panel (right):** Fluid width (`flex: 1`). Shows full details for the selected job. Scrolls independently.

### Mobile (<768px)

Panels stack vertically. List on top, detail below. Tapping a job scrolls the viewport to the detail section. A "back to list" link at the top of the detail section scrolls back up.

Both panels collapse to `100%` width. The detail section is hidden until a job is selected. A small "Back to jobs" link (mono, pencil grey, with left arrow) appears at the top of the detail section on mobile, scrolling back to the list on click.

## Visual Identity

All values from `.claude/references/DESIGN.md` (Architectural Schematic).

### Colors

| Role | Value |
|-|-|
| Background | `#F9F9F9` |
| Surface (detail panel, hover) | `#FCFCFC` |
| Text primary | `#222222` |
| Text secondary / muted | `#808080` |
| Accent (interactive, selected) | `#5B9BD5` |
| Accent secondary (salary) | `#4A90E2` |
| Border | `#ddd` |
| Border light | `#eee` |

### Typography

| Role | Font | Weight | Size |
|-|-|-|-|
| Page title | Helvetica Neue | 700 | 22px |
| Detail title | Helvetica Neue | 700 | 24px |
| List item title | Helvetica Neue | 500 | 13px |
| Body / summary | Helvetica Neue | 400 | 14px / 1.75 |
| Company labels | Helvetica Neue | 600 | 10-12px, uppercase, tracked |
| Metadata (salary, tags, filters, counts) | JetBrains Mono | 400-500 | 10-11px |
| Apply button | Helvetica Neue | 600 | 14px |

### Architectural Accents

Light touches, not full blueprint:

- **Crosshair motif:** CSS pseudo-elements forming a `+` shape next to the header title, in blueprint blue.
- **Dimension-marker dividers:** Dashed 1px lines with tick marks and uppercase labels (e.g., `--- Description ---`) separating sections in the detail panel.
- **Fine lines:** All borders 1px solid. No heavy shadows (max `0 2px 12px rgba(0,0,0,0.06)`).
- **No decorative gradients, no emojis, no pure black.**

## Components

### Header (list panel top)

- Title: crosshair motif + "HN Jobs" + `/ {count}` in mono
- Search input: 1px border, search icon left, 4px radius
- Filter pills: mono font, 3px radius, active = dark border + dark text, inactive = grey border + grey text

### Job List Items

Each item shows:
- Company name (uppercase, tracked, 10px)
- Role title (13px, truncated with ellipsis)
- Bottom row: location (left) + salary in mono blue (right, only if present)

States:
- Default: transparent background
- Hover: `#FCFCFC` background
- Selected: `#F0F6FC` background + 2px blueprint-blue left border, company name turns blue

Clicking a list item updates the detail panel. First item selected on page load.

### Detail Panel

Sections in order:
1. **Company** — uppercase, blueprint blue, tracked
2. **Title** — 24px, 700 weight
3. **Badges row** — location, YOE (if present), salary badge (blue tint background, only if present)
4. **Dimension-marker divider** — dashed line labeled "Description"
5. **Summary** — 14px, `#555`, max-width 600px, 1.75 line height
6. **Stack section** — label "Stack" + skill tags in mono with 1px borders
7. **Apply button** — blueprint blue fill, white text, 12px 32px padding, `0.5rem` radius, hover: darken + lift shadow + translateY(-1px), active: translateY(0)
8. **HN link** — secondary mono link "View on Hacker News"
9. **Footer** — dashed top border, poll date + source in mono grey

### Apply Button

The primary CTA. Design details:
- Background: `#5B9BD5`
- Text: white, 14px, weight 600
- Padding: 12px 32px
- Includes arrow-up-right icon (14px SVG)
- Hover: background darkens to `#4A8BC5`, box-shadow `0 2px 8px rgba(91,155,213,0.25)`, translateY(-1px)
- Active: translateY(0)
- Links to `source_url` if available, otherwise HN item URL

### Empty State

Centered text when search/filter yields no results:
- "No jobs match" in 18px
- "Try a different query or filter" in 13px mono grey

## Interaction

### Search

Text input filters jobs in real-time against all fields (title, company, location, summary, salary, skills). Case-insensitive substring match. Same logic as current implementation.

### Filters

Same filter set as current: All, Remote, SF, NYC, Engineering, Founding, Salary. Single-select (clicking one deactivates others). "All" is the default.

### Job Selection

Clicking a list item selects it (visual state change) and renders its data in the detail panel. On page load, the first job in the filtered list is auto-selected.

### Animation

Per brand guidelines:
- Card/item entry: fade + translateY(16px to 0) over 420ms ease-out, staggered 80ms between items
- Hover: color/shadow shift over 200ms
- Only `transform` and `opacity` animated

## Data

No changes to the `JOBS` array or data structure. The page reads the same inline JSON. All rendering logic stays client-side JavaScript.

## Files Changed

Only `jobs.html`. Single self-contained file (inline CSS + JS), same as current.

## Out of Scope

- Multi-select filters / sort controls
- Keyboard navigation
- Dark mode
- External CSS/JS files
- Changes to the Python pipeline or data extraction
