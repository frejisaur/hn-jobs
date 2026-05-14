# Design System: Blueprint & Flow

Brand guidelines for UI work in the hn-jobs project. Derived from the "Claude Code Masterclass" visual language: the tension between **deterministic scaffolding** (grids, blueprint lines, rigid frames) and **stochastic flow** (organic watercolor shapes, soft gradients).

Use this file as the `brandGuidelines` input when invoking the `frontend-design` skill.

---

## Core Concept

Every interface should feel like a **technical blueprint that something alive is flowing through**. Rigid structure (grids, dashed containers, monospace labels) coexists with organic softness (gradient blobs, flowing color, rounded forms). Neither dominates -- the design lives in the tension.

---

## Color Palette

### Foundations

| Token | Hex | Usage |
|-|-|
| `--bg-primary` | `#EDE8DE` | Page background -- warm parchment/cream |
| `--bg-secondary` | `#F5F0E8` | Card/panel backgrounds, slightly lighter |
| `--text-primary` | `#2D2926` | Headlines, body text -- warm near-black |
| `--text-secondary` | `#6B6560` | Subtitles, captions, muted text |
| `--text-tertiary` | `#9C9590` | Disabled states, placeholder text |

### Accents (the watercolor palette)

| Token | Hex | Usage |
|-|-|-|
| `--accent-peach` | `#D4A08A` | Primary accent -- warm salmon/peach |
| `--accent-peach-light` | `#E8C8B8` | Peach tint for backgrounds, hover states |
| `--accent-lavender` | `#B8A0C8` | Secondary accent -- soft mauve/purple |
| `--accent-lavender-light` | `#D4C4E0` | Lavender tint for backgrounds |
| `--accent-sand` | `#D4C4A8` | Tertiary accent -- warm tan/sand |
| `--accent-coral` | `#C86830` | Connector lines, active states, links |

### Structural

| Token | Hex | Usage |
|-|-|-|
| `--grid-line` | `#C8C0B4` | Blueprint grid lines, subtle borders |
| `--grid-line-light` | `#DDD8D0` | Faint grid marks, reference ticks |
| `--surface-dark` | `#2D2926` | Dark bars, pills, deterministic elements |
| `--surface-dark-text` | `#EDE8DE` | Text on dark surfaces |
| `--border-dashed` | `#A8A098` | Dashed conceptual containers |

### Gradient definitions

```css
/* Watercolor blob gradient -- use for stochastic/AI elements */
--gradient-flow: linear-gradient(
  135deg,
  var(--accent-sand) 0%,
  var(--accent-peach) 40%,
  var(--accent-lavender) 100%
);

/* Subtle page grain overlay */
--gradient-parchment: radial-gradient(
  ellipse at 30% 50%,
  rgba(212, 160, 138, 0.08) 0%,
  transparent 70%
);
```

---

## Typography

### Font Stack

| Role | Font | Fallback | Weight |
|-|-|-|-|
| Headlines | **Libre Baskerville** | Georgia, serif | 700 |
| Subtitles | **Libre Baskerville** | Georgia, serif | 400, italic |
| Body | **Source Sans 3** | system-ui, sans-serif | 400, 600 |
| Labels/Code | **IBM Plex Mono** | monospace | 400, 500 |

```html
<!-- Google Fonts import -->
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
```

### Scale

| Token | Size | Line Height | Usage |
|-|-|-|-|
| `--text-display` | 2.5rem (40px) | 1.2 | Page titles |
| `--text-h1` | 1.75rem (28px) | 1.3 | Section headers |
| `--text-h2` | 1.25rem (20px) | 1.35 | Card titles, sub-headers |
| `--text-body` | 1rem (16px) | 1.6 | Body text |
| `--text-small` | 0.875rem (14px) | 1.5 | Captions, metadata |
| `--text-label` | 0.75rem (12px) | 1.4 | Grid references, badges (monospace) |

### Rules

- Headlines are **always serif** (Libre Baskerville). No exceptions.
- Technical annotations, status labels, and grid references use **monospace** (IBM Plex Mono) at `--text-label` size, uppercase, with `letter-spacing: 0.08em`.
- Body copy uses **Source Sans 3** for readability at smaller sizes.
- Subtitles under headlines use Libre Baskerville regular (not bold), often italic.

---

## Design Patterns

### 1. Blueprint Grid

The underlying structure. Faint grid lines on the parchment background create a technical-drawing feel.

```css
.blueprint-grid {
  background-image:
    linear-gradient(var(--grid-line-light) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-line-light) 1px, transparent 1px);
  background-size: 40px 40px;
}
```

Optional: add **grid reference markers** (e.g., `A1`, `B3`) in the corners of major sections using monospace labels at low opacity.

### 2. Watercolor Blobs (Stochastic Elements)

Organic, soft-edged shapes representing AI/stochastic processes. Implemented as CSS gradient blobs with blur.

```css
.flow-blob {
  background: var(--gradient-flow);
  border-radius: 60% 40% 50% 45% / 45% 55% 40% 60%;
  filter: blur(2px);
  opacity: 0.7;
  animation: morph 8s ease-in-out infinite alternate;
}

@keyframes morph {
  0%   { border-radius: 60% 40% 50% 45% / 45% 55% 40% 60%; }
  50%  { border-radius: 45% 55% 40% 60% / 60% 40% 55% 45%; }
  100% { border-radius: 50% 45% 55% 40% / 40% 60% 45% 55%; }
}
```

Use for: AI processing states, loading indicators, background decorations on feature sections.

### 3. Deterministic Containers

Rigid, dashed-border boxes that frame content. Represent structure, specs, wrappers.

```css
.deterministic-container {
  border: 1.5px dashed var(--border-dashed);
  padding: 1.5rem;
  background: var(--bg-secondary);
}

/* Solid variant for confirmed/final states */
.deterministic-container--solid {
  border: 1.5px solid var(--text-primary);
  background: var(--bg-secondary);
}
```

### 4. Film Strip / Pipeline

Horizontal workflow stages with sprocket-hole decoration along top and bottom edges. Each stage contains a watercolor blob.

```css
.pipeline {
  display: flex;
  gap: 0;
  border-top: 2px solid var(--text-primary);
  border-bottom: 2px solid var(--text-primary);
  /* Sprocket holes via repeating radial gradient on pseudo-elements */
}

.pipeline-stage {
  flex: 1;
  border-right: 1.5px solid var(--grid-line);
  padding: 1.5rem;
  position: relative;
}
```

### 5. Connector Lines

Coral/orange lines connecting elements, evoking circuit-board traces.

```css
.connector {
  stroke: var(--accent-coral);
  stroke-width: 2;
  fill: none;
}

/* Right-angle connections (circuit-board style) */
.connector--circuit {
  stroke-linejoin: round;
  stroke-linecap: round;
}
```

Use SVG for complex connector paths. Prefer right-angle turns over curves.

### 6. Dark Pills / Badges

Small dark labels for status, categories, or phase markers.

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  background: var(--surface-dark);
  color: var(--surface-dark-text);
  font-family: 'IBM Plex Mono', monospace;
  font-size: var(--text-label);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  border-radius: 2px;
}
```

### 7. Insight Callouts

Boxed insight or note at the bottom of a section.

```css
.insight {
  border: 1px solid var(--grid-line);
  background: var(--bg-secondary);
  padding: 1rem 1.25rem;
  font-family: 'Libre Baskerville', serif;
  font-style: italic;
  font-size: var(--text-small);
  color: var(--text-secondary);
}

.insight::before {
  content: 'Insight:';
  font-weight: 700;
  font-style: normal;
  margin-right: 0.5em;
  color: var(--text-primary);
}
```

---

## Spacing

Use an 8px base grid. All spacing values should be multiples of 8.

| Token | Value |
|-|-|
| `--space-xs` | 0.25rem (4px) |
| `--space-sm` | 0.5rem (8px) |
| `--space-md` | 1rem (16px) |
| `--space-lg` | 1.5rem (24px) |
| `--space-xl` | 2.5rem (40px) |
| `--space-2xl` | 4rem (64px) |

---

## Shadows & Depth

Minimal. The blueprint aesthetic is flat by nature. Use shadows sparingly and only for elevated interactive elements.

```css
--shadow-subtle: 0 1px 3px rgba(45, 41, 38, 0.06);
--shadow-card: 0 2px 8px rgba(45, 41, 38, 0.08);
--shadow-elevated: 0 4px 16px rgba(45, 41, 38, 0.12);
```

---

## Motion

### Principles

- **Structural elements** (grids, containers, lines) move precisely: ease-out, short duration (150-250ms).
- **Organic elements** (blobs, gradients) move slowly and fluidly: ease-in-out, long duration (600ms-2s+).
- Page loads use staggered reveals with `animation-delay` increments of 80-120ms.

```css
--ease-precise: cubic-bezier(0.25, 0.1, 0.25, 1);
--ease-organic: cubic-bezier(0.4, 0, 0.2, 1);
--duration-fast: 150ms;
--duration-normal: 250ms;
--duration-slow: 600ms;
--duration-ambient: 2000ms;
```

---

## Borders & Radii

| Element | Radius |
|-|-|
| Containers, cards | `2px` (sharp, technical) |
| Badges, pills | `2px` |
| Buttons | `2px` |
| Watercolor blobs | Organic `border-radius` (see pattern above) |
| Avatar/icon circles | `50%` |

Almost everything is sharp-cornered. The only roundness comes from organic blob elements.

---

## Do / Don't

**Do:**
- Use the warm parchment background everywhere -- never pure white or pure black backgrounds
- Pair rigid structure (grid, dashes, monospace) with organic softness (blobs, gradients)
- Use coral `--accent-coral` for interactive elements and connections
- Let the design breathe -- generous whitespace on the warm background
- Use film-strip/sprocket decoration for sequential workflows
- Add subtle grid-reference labels in corners of major sections

**Don't:**
- Use rounded corners on structural elements (keep them at 2px max)
- Use drop shadows heavily -- this is a flat blueprint aesthetic
- Use bright saturated colors -- the palette is muted, warm, and organic
- Use generic sans-serif fonts for headlines
- Mix cool-toned grays with the warm palette
- Add gratuitous animation to structural elements -- save fluidity for organic shapes
