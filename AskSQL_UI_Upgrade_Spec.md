# AskSQL — UI Upgrade Specification

> **Purpose:** This document tells an AI coding assistant exactly how to redesign AskSQL's current UI. It covers the current state, the target design direction, exact component-level changes, and a rollout plan. Treat this as a requirement doc, not inspiration — but where a visual judgment call is needed, the assistant should look at the referenced live page directly rather than guess.

---

## 0. Fix Before Restyling — Known Bug

**The Generated SQL display is currently broken.** In the current build, a query like `SELECT COUNT(order_id) FROM orders` renders as:
```
SELECTSELECTCOUNT FROMCOUNT(order_id) FROM orders
```
This looks like a syntax-highlighting bug — SQL keywords (`SELECT`, `FROM`, `COUNT`) are being rendered twice, likely because a syntax-highlighter (e.g., Prism/highlight.js) is being applied on top of text that's already had manual keyword-wrapping applied, or the raw string is being tokenized and concatenated twice. **Fix this first.** Check the `SqlDisplay.jsx` component for double-processing of the SQL string (e.g., manually wrapping keywords in `<span>` tags AND passing the same string through a syntax-highlighting library). A UI restyle on top of a visibly broken SQL renderer will look worse, not better, in a demo.

---

## 1. Current State (What Exists Today)

Based on the current build (screenshots reviewed):
- Dark theme (navy/near-black background, `#0b0f1a`-ish), purple/blue gradient headline, blue accent buttons
- Layout: left sidebar (Schema Browser + History), main content area (hero + input box + example question chips + explanation + generated SQL + results table)
- Functional pieces present: schema browser with expandable table descriptions, query history list, plain-English explanation card, collapsible SQL block with "Copy SQL" and "Hide" controls, results table with CSV export
- Typography: fairly generic system sans-serif, decent hierarchy but no distinct visual identity
- Overall impression: functional developer-tool aesthetic, but generic — could be mistaken for a template dashboard

## 2. Target Design Direction

**Reference:** [Oracle Developer — IDE page](https://www.oracle.com/in/developer/ide-developers/).

**Correction from an earlier draft of this spec:** an earlier version of this document assumed the Oracle page used a light, white-background corporate style. That was wrong — a guess made without actually viewing the rendered page, defaulting to a generic "corporate site = light theme" stereotype. Screenshots of the actual page show a **dark slate/charcoal theme** as the primary look, with light sections used only for specific CTA/footer blocks. The direction below reflects what's actually on the page.

### What the reference page actually looks like:
- **Primary background:** dark slate/charcoal-gray (not black, not navy — a muted blue-gray, roughly `#3D4A52`–`#4A5560` range), used across the hero and most content sections
- **Headline font:** an elegant **serif** typeface for large headlines ("Integrated Development Environment (IDE)", "Featured IDEs", "Follow Oracle Developers") — a distinct, editorial feel rather than a generic sans-serif dashboard look
- **Body/UI font:** clean sans-serif for body copy, nav, buttons, tabs
- **Accent color:** warm gold/amber (used for the small underline divider beneath the hero headline, and for "Learn more and install" links inside dark cards) plus a **coral-red** geometric accent shape (large rounded/angular blob shapes bleeding into the hero and section breaks — decorative, not functional UI)
- **Tab-style navigation:** "Featured IDEs" section uses a simple underline-tab pattern (VS Code | IntelliJ | Eclipse | Netbeans | JDeveloper) with a bold-white active tab and a thin underline indicator
- **Cards within dark sections:** slightly lighter-than-background card panels (e.g., the "Oracle NoSQL database connector" card), white headline text, light gray body text, gold link at the bottom — no heavy borders, minimal shadow; separation comes mostly from the subtle background tone shift
- **Light sections used selectively:** the "Oracle Cloud Free Tier" CTA band and the footer switch to a white/off-white background with a solid black button and a serif "Follow Oracle Developers" headline — the page deliberately alternates dark → light → light for rhythm and to make the final CTA/footer feel distinct, rather than being dark end-to-end
- **Icons:** simple monochrome/brand-colored social icons in the footer, minimal iconography elsewhere

### Key characteristics to bring into AskSQL:
1. **Keep AskSQL's dark theme as primary** (this now aligns with the reference rather than fighting it). Refine the existing near-black palette toward a similar warmer slate-gray family for a more editorial feel, rather than pure `#0B0F1A`.
2. **Introduce a serif display font for headlines only** ("Ask your database anything", section headers like "Schema Browser", "Results") while keeping clean sans-serif for body text, buttons, and data — this single change does a lot to shift AskSQL from "generic dashboard" toward "designed product."
3. **Accent colors: yellow/gold as primary, red as secondary** (per developer preference — no blue/indigo/purple). Gold/yellow drives all primary interactive elements (buttons, active states, links, focus states). Red is reserved for negative/destructive/urgent states (delete actions, failure badges) plus optional decorative shapes — this keeps the palette confident rather than alarm-heavy, since red would read as "something's wrong" if overused on neutral UI.
4. **Off-white replaces cool white/gray for text and the optional light section** — warmer than the previous near-white tones, ties together with the gold/red palette rather than clashing with it.
5. **Card treatment inside the dark theme**: cards are a subtly lighter tone than the page background (not white-on-dark, not heavily bordered) — apply this to schema browser entries and history entries so they read as distinct panels without needing strong borders or shadows.
6. **Selective light section for rhythm**: consider one light (warm off-white) band somewhere in the AskSQL flow (e.g., around a summary/export moment) rather than converting the whole page.
7. **Tab-style navigation pattern**: adapt the underline-tab style for any place AskSQL has grouped/switchable content (e.g., History and Schema Browser could become tabs of one panel instead of two always-visible sidebars — optional, evaluate feasibility, don't force it if it hurts usability).
8. **Decorative geometric accent shapes**: optional, low-priority — a subtle red abstract shape in the hero background (purely aesthetic, not functional) can add visual distinctiveness, but keep this nice-to-have.

---

## 3. Color Palette (Dark Theme — Primary, Matches Reference Direction)

**Accent direction (updated per developer request):** dropping blue/indigo/purple entirely. Primary interactive accent is now **yellow/gold**, with **red** as the secondary/decorative accent (upgraded from purely-decorative to also covering a few functional states like destructive actions and failure badges), and an **off-white** replacing the previous cool white/gray text tones for a warmer overall feel.

| Token | Value (starting point) | Usage |
|---|---|---|
| `--bg-primary` | `#3D4550` (warm slate) | Page background |
| `--bg-card` | `#454E5A` (subtly lighter than page background) | Card backgrounds — schema entries, history entries |
| `--border-subtle` | `rgba(255,255,255,0.08)` | Faint card separation, used sparingly — prefer background tone-shift over borders |
| `--text-primary` | `#F5F0E6` (warm off-white) | Headlines, primary text |
| `--text-secondary` | `#C2BAA8` (muted warm gray) | Descriptions, metadata, timestamps |
| `--accent-primary` | `#E8B923` (confident yellow/gold) | Primary buttons, active states, links, interactive highlights — replaces the old indigo |
| `--accent-primary-hover` | `#C99A16` (darker gold) | Button hover state |
| `--accent-secondary` | `#C1443A` (warm red) | Secondary accent — destructive actions (e.g., delete history), failure badges, decorative shapes, "hot"/urgent states |
| `--success` | `#4ADE80` | "Success" history badges — kept green since red is now taken by the failure/destructive role, and green-vs-red is the most universally readable success/fail pairing |
| `--code-bg` | `#1E1E2E` | Generated SQL block background (kept cool-dark for IDE-style contrast against the warm page) |
| `--code-text` | `#E5E7EB` | SQL text color |
| `--shadow-card` | `0 2px 8px rgba(0,0,0,0.25)` | Card elevation |

**Optional light section** (for the one selective light band, Section 2 point 5 — e.g., a results/export moment):
| Token | Value |
|---|---|
| `--bg-light-section` | `#FAF6EE` (warm off-white, not stark `#FFFFFF`) |
| `--text-on-light` | `#2A2620` |
| `--cta-on-light` | `#C1443A` (the red accent works well as a bold solid button on a light background — direct visual pop) |

**Light mode toggle** (secondary, optional): reuse this same light-section palette as the base and extend it, rather than maintaining two unrelated palettes.

**Where NOT to use each accent:**
- Yellow/gold (`--accent-primary`) is the workhorse — buttons, active tab underline, links, focus rings, badges for counts.
- Red (`--accent-secondary`) stays limited to negative/urgent/destructive contexts (delete, failure, error) plus small decorative shapes — don't use it for the primary "Run Query" button or other positive/neutral actions, or the app will read as alarm-heavy rather than confident.
- Off-white is for text and the optional light section background — don't use it as a card background in the dark theme (cards stay `--bg-card`, a lighter *slate*, not off-white, or they'll look like stray white boxes floating on a dark page).

---

## 4. Typography

| Element | Spec |
|---|---|
| Headline font | A serif display face — e.g., `Georgia`, `"Playfair Display"`, or `"Source Serif 4"` — used ONLY for large headlines (hero title, section headers like "Schema Browser"/"Results"), matching the reference page's editorial serif treatment |
| Body/UI font | `Inter` (or system-ui fallback) for body text, buttons, nav, tabs, form inputs — keep this sans-serif, don't serif-ify everything |
| Code font | `JetBrains Mono` or `Fira Code` for SQL/code blocks |
| Hero headline | Serif, 40-48px, weight 500-600 (serif faces often look better slightly lighter than 700), tight line-height (1.1) |
| Hero subtext | Sans-serif, 16-18px, weight 400, `--text-secondary`, max-width ~600px, centered |
| Section headers (e.g. "Schema Browser," "Results") | Serif, 20-24px, weight 500, `--text-primary` — NOT the small-caps uppercase treatment from the earlier draft; the reference uses full-size serif headers, not tiny uppercase labels |
| Card titles (table names, history entries) | Sans-serif, 15-16px, weight 600, `--text-primary` |
| Body/description text | Sans-serif, 14px, weight 400, `--text-secondary` |
| SQL code block | Monospace, 14px, 1.6 line-height |
| Small gold underline divider | A short (~48px), 2-3px thick `--accent-primary` bar beneath major headlines — direct nod to the reference page's headline treatment |

---

## 5. Component-Level Redesign

### 5.1 Header
- Keep: logo/lightning-bolt icon + "AskSQL" wordmark, "API Connected" status pill (top right)
- Change: shift header background to `--bg-primary` warm slate; status pill keeps its dark-mode-friendly treatment (`bg: rgba(74,222,128,0.15), text: --success`)
- Add: an optional light/dark toggle icon button next to the status pill, if you choose to keep the selectable light mode (Section 3) — not required

### 5.2 Hero Section
- Keep existing copy ("Ask your database anything" / subtext / "Powered by Llama 3 + ChromaDB RAG" pill)
- Change: hero headline switches to the serif display font (Section 4), with a short `--accent-primary` (gold) underline divider beneath it
- "Powered by..." pill: keep dark, subtle border (`border: 1px solid rgba(255,255,255,0.15)`), text in `--accent-primary` gold instead of the old blue/purple gradient
- Optional: a subtle red (`--accent-secondary`) decorative geometric shape in the hero background (Section 2, point 7) — low priority

### 5.3 Query Input Card
- Card background: `--bg-card`, soft shadow (`--shadow-card`), rounded corners (12px)
- "Run Query" button: solid `--accent-primary` (gold) background, dark text (`#2A2620`, not white — white-on-gold has weak contrast; dark text on gold reads much better) — this replaces the old indigo button
- Example question chips: `bg: --bg-card, border: 1px solid --border-subtle, text: --text-secondary`; hover state shifts border/text to `--accent-primary` gold

### 5.4 Schema Browser Sidebar
- Each table entry becomes its own card: `--bg-card` background, subtle shadow, rounded corners, small icon + table name (sans-serif, weight 600) + truncated description (`--text-secondary`)
- Expand/collapse chevron stays; expanded state shows full column list with the improved schema descriptions
- Section header "Schema Browser" restyled per Section 4 (serif, 20-24px) with the count badge as a small rounded pill in `--accent-primary` gold, dark text

### 5.5 History Sidebar
- Each history entry as its own `--bg-card` panel with subtle-shadow treatment
- Success badge: `--success` green pill (kept as-is — green/red is the clearest success/fail pairing); failure badge: `--accent-secondary` red pill at reduced opacity/background tint — this is the main functional (not just decorative) use of red
- Delete/trash icon (seen in the History header in your screenshots) also uses `--accent-secondary` red on hover, since it's a destructive action
- Timestamp in `--text-secondary`, right-aligned as now

### 5.6 Plain-English Explanation Card
- Left-accent-border pattern: recolor from blue to `--accent-primary` gold
- Card background: `--bg-card`
- Icon (currently a "?" in a circle) — keep, recolor to `--accent-primary` gold

### 5.7 Generated SQL Block
- Keep `--code-bg` (`#1E1E2E`) for IDE-style contrast
- Fix the duplication bug (Section 0) before or during this restyle
- Add proper SQL syntax highlighting — consider gold for keywords, a soft red/coral for string literals, and off-white for identifiers, to tie the code block into the new palette rather than using generic syntax-highlighter defaults
- Keep "Copy SQL" and "Hide" controls, restyle as ghost/outline buttons using `--text-secondary` with `--accent-primary` gold on hover

### 5.8 Results Table
- `--bg-card` container, rounded corners
- Row hover state: subtle lightening relative to `--bg-card` (4-6% lighter)
- Column headers: sans-serif, `--text-secondary`, small-caps/uppercase treatment
- "CSV" export button restyled as outline/ghost button, gold accent on hover
- Row count badge ("1 row") restyled as small pill in `--accent-primary` gold, dark text

---

## 6. Layout & Spacing

- Increase overall page padding: minimum 24-32px outer margins (current build feels edge-to-edge/cramped in places)
- Increase gap between cards: 16-20px vertical rhythm between stacked cards (schema entries, history entries)
- Sidebar width: keep roughly as-is, but add internal padding within each sidebar card so content doesn't touch card edges
- Main content max-width: cap at ~1200px and center on very wide screens rather than stretching full-bleed

---

## 7. Implementation Plan

### Step 1 — Fix the SQL rendering bug (Section 0)
Do this before any visual changes so you're not restyling broken output.

### Step 2 — Introduce design tokens
Set up CSS variables (Section 3 palette, Section 4 typography) as a Tailwind theme extension (`tailwind.config.js`) or CSS custom properties, so every component pulls from the same source rather than hardcoded colors. This also keeps the door open for a light-mode toggle later without a rewrite, if Open Question 2 is answered "yes" — swap the token set based on a `data-theme` attribute or Tailwind's `dark:` variant.

### Step 3 — Rebuild components card-by-card
Work in this order (lowest risk to highest visual impact):
1. Header + hero (low risk, high visibility — good warm-up)
2. Query input card + example chips
3. Schema browser cards
4. History cards
5. Explanation card
6. Generated SQL block (bug fix + restyle together)
7. Results table

### Step 4 — (Optional) Add a light/dark toggle
Only build this if Open Question 2 is answered "yes." If so, implement last, once all components support both token sets — easier to verify both themes work once the component styles are already token-driven rather than hardcoded. If the answer is "no," skip this step — the dark theme refinement from Steps 1-3 already delivers the target look.

### Step 5 — Cross-check against the reference
Open the [Oracle IDE developer page](https://www.oracle.com/in/developer/ide-developers/) side-by-side with the updated AskSQL UI and sanity-check: does it feel like it belongs to the same design family (warm dark palette, serif headline treatment, card tone-shifts rather than borders)? It should NOT look like an Oracle-branded clone — no Oracle logo styling, no red-as-primary-action-color — just share the same design *pattern* (dark editorial theme, serif+sans pairing, selective light rhythm) rather than matching brand identity.

---

## 8. What NOT to Change

- Don't touch the underlying functional logic (query flow, validator, retry loop) — this is a pure UI/UX pass
- Don't force a full light-mode conversion — the reference itself is primarily dark; a light toggle is optional, not required by this brief
- Don't overuse red — it's reserved for destructive/failure/urgent states plus light decorative use; if red starts appearing on primary buttons or neutral UI, the app will read as alarm-heavy rather than confident
- Don't serif-ify body text, buttons, or data — serif is for headlines only; overusing it will hurt readability and make the UI feel less like a functional dev tool
- Don't add animation/motion complexity beyond simple hover states and card transitions — keep scope realistic for a solo 4th-year student's timeline

---

## 9. Open Questions — **[ASK FIRST]**

1. Confirm serif font choice — `Georgia` is a safe, always-available fallback with zero setup; `"Playfair Display"` or `"Source Serif 4"` (Google Fonts) look closer to the reference's elegant serif but require adding a font import. Pick based on how much polish-vs-effort tradeoff is worth it.
2. Confirm whether a full light-mode toggle is wanted at all, given the reference itself doesn't really have one (it just alternates dark/light by section) — a toggle adds real implementation work (Section 7, Step 4) that may not be worth it if the dark theme alone already hits the target look.
3. Should the SQL syntax highlighting use a library (e.g., `react-syntax-highlighter`, `prism-react-renderer`) or a lightweight custom tokenizer? A library is faster to implement correctly and avoids re-introducing the Section 0 bug.
4. Decide whether to attempt the optional tab-style History/Schema-Browser merge (Section 2, point 6) or leave them as two separate sidebars — only pursue if it doesn't hurt at-a-glance usability, since simultaneous visibility of both may matter more for a demo than a stylistic tab pattern.

---

*End of specification. Fix Section 0 first. Then proceed component-by-component per Section 7.*
