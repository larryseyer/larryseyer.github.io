# Larry Seyer GitHub Pages Website

This repository hosts the personal website for Larry Seyer, served via GitHub Pages at `larryseyer.github.io`.

## Design System

The site uses **"The Architect"** design system:
- True black (#000000) background with amber (#f59e0b) accent
- Space Grotesk for headlines, Inter for body, JetBrains Mono for code
- Sharp corners, generous whitespace, minimal decoration
- Professional, no-compromise aesthetic

## Structure

```
/
├── index.html                    # Homepage
├── css/
│   └── style.css                 # Design system (CSS custom properties)
├── js/
│   └── main.js                   # Navigation and scroll animations
├── images/
│   └── projects/                 # Project screenshots and logos
├── pages/
│   ├── work.html                 # Credentials and expertise
│   ├── projects.html             # Projects hub
│   ├── live.html                 # The Larry Seyer Show + podcast
│   ├── connect.html              # Social and contact links
│   └── projects/
│       ├── otto.html             # OTTO - Organic Tempo and Time Orchestrator
│       ├── jtf-news.html         # JTF News - Just The Facts
│       ├── grim.html             # GRIM - Scene-based loop station
│       ├── icandy.html           # iCandy - REAPER theme
│       ├── showswitcher.html     # ShowSwitcher - Camera automation
│       └── midi2button.html      # MIDI2Button - MIDI trigger module
└── docs/
    └── plans/                    # Design and implementation plans
```

## Customization

All design tokens are CSS custom properties in `css/style.css`:
- `--color-*` for colors
- `--font-*` for typography
- `--space-*` for spacing

## Development

```bash
python3 -m http.server 8000
# Visit http://localhost:8000
```

## Git Workflow

- Commit locally as work progresses
- **Do NOT push until explicitly instructed** by the user
- Main branch deploys automatically to GitHub Pages once pushed

## GitHub Repository Links

Projects link to these repos. All are public — verify with
`gh repo view <owner/name> --json visibility` before adding a link, because a private or
deleted repo 404s for visitors:

- JTF News: https://github.com/larryseyer/jtfnews
- JTF News iOS app: https://github.com/larryseyer/jtfnewsapp
- iCandy: https://github.com/larryseyer/iCandy
- ShowSwitcher: https://github.com/larryseyer/companion-module-generic-showswitcher
- MIDI2Button: https://github.com/larryseyer/midi2button
- ACIM Daily Minute: https://github.com/larryseyer/ACIMDailyMinuteApp

**Do not link OTTO, IDA, or GRIM to GitHub.** OTTO and IDA are private and
`larryseyer/GRIM-for-Reaper` does not exist; all three are proprietary products and their
pages carry a Licensing section instead of a source link.

## Licensing Claims

The product family moved from AGPLv3 to proprietary on 2026-08-01. Before writing or editing
any licensing sentence on a project page, read that project's `LICENSE` file and match it. The
"versions released before 2026 remain under the AGPLv3" sentences on the OTTO and IDA pages are
deliberate — those grants cannot be revoked, and removing them would make the pages inaccurate
again in the other direction.
