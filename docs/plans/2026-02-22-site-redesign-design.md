# Larry Seyer Website Redesign

**Date:** 2026-02-22
**Status:** Approved
**Approach:** "The Architect" - Clean precision, intentional design

---

## Design Philosophy

**Core message:** No compromise. Ultimate solution finder. Precision and professionalism.

**Brand shift:** From "industry veteran with famous clients" to "forward-thinking technologist bridging audio expertise with AI and programming."

**Voice:** Confident, direct, zero filler.

---

## Color System

| Role | Value | Usage |
|------|-------|-------|
| Background | `#000000` | Page background |
| Surface | `#0a0a0a` | Cards, elevated elements |
| Border | `#1a1a1a` | Subtle dividers, card edges |
| Text Primary | `#ffffff` | Headlines, important text |
| Text Secondary | `#888888` | Body text, descriptions |
| Accent | `#f59e0b` | Links, buttons, highlights |
| Accent Hover | `#fbbf24` | Hover states |

---

## Typography

| Element | Font | Weight | Size | Tracking |
|---------|------|--------|------|----------|
| Headlines | Space Grotesk | 700 | 3-5rem | -0.02em |
| Subheadlines | Space Grotesk | 500 | 1.5rem | -0.01em |
| Body | Inter | 400 | 1rem | normal |
| Labels/Tags | Inter | 600 | 0.75rem | 0.05em |
| Code/Technical | JetBrains Mono | 400 | 0.875rem | normal |

**Headline style:** Short. Declarative. No fluff.

---

## Layout Principles

- 12-column grid with generous gutters
- Content rarely spans full width
- Ample vertical spacing (8-12rem between sections)
- Asymmetric compositions
- No rounded corners (sharp = precise)

---

## Site Structure

```
/                          → Homepage
/work/                     → Credentials, awards, film work
/projects/                 → Project hub grid
/projects/otto/            → OTTO - Organic Tempo and Time Orchestrator
/projects/jtf-news/        → JTF News - Fact-only live stream
/projects/grim/            → GRIM - Scene-based loop station
/projects/icandy/          → iCandy - REAPER theme
/projects/showswitcher/    → ShowSwitcher - Camera automation
/projects/midi2button/     → MIDI2Button - MIDI trigger module
/live/                     → The Larry Seyer Show
/connect/                  → Social links, contact
```

**Total: 11 pages**

---

## Homepage Sections

1. **Hero** — Name + two-line positioning statement
2. **Capabilities** — 3-4 cards (Audio Engineering, Software Development, AI & Audio Innovation, Live Production)
3. **Philosophy** — One powerful statement block
4. **Current Focus** — Brief on OTTO, GRIM, JTF News
5. **Footer** — Social links, copyright

---

## Project Page Template

Each project page follows consistent structure:

1. **Hero** — Project name + one-line description
2. **Status Badge** — Active Development / Released / Maintained
3. **The Problem** — What this solves (2-3 sentences max)
4. **Key Features** — Bulleted, scannable
5. **Screenshots** — If available (user to provide)
6. **GitHub Link** — Prominent button

---

## Visual Details

**Borders & Lines:**
- Thin horizontal rules (1px #1a1a1a) to separate sections
- Cards have subtle borders, not backgrounds
- No rounded corners

**Hover States:**
- Links: color shift to amber, no underline
- Cards: border → amber, scale(1.01)
- Buttons: background inverts

**Animations:**
- Fade-in on scroll (opacity 0→1, translateY 20px→0)
- Transitions: 200ms ease-out
- No flashy effects

**Mobile:**
- Hamburger menu
- Same typography relationships, reduced sizes
- Stack layouts vertically

---

## Content Removed

- Notable Artists / name-dropping sections
- Long bio paragraphs
- "What to Expect" type fluff
- APC-40 Realearn config (internal only)

---

## Assets Needed

- Screenshots for each project (user to provide)
- Existing logo (keep as-is)
