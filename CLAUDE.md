# Larry Seyer GitHub Pages Website

This repository hosts the personal website for Larry Seyer, served via GitHub Pages at `larryseyer.github.io`.

## Design System

The site uses the **"Stage Light"** design system, replacing the earlier black-and-amber
"Architect" system. The palette comes from the show's own lighting rig:

- Near-black violet ground (#0a0713) under a fixed two-source wash — magenta (#ff3d92) from
  house left, cyan (#3ddcff) from house right, warm spot (#ffb648) between them
- Bricolage Grotesque for headlines, Public Sans for body, Azeret Mono for labels and data
- Rounded corners, pill buttons, cards that light up under the cursor

Every page shares one stylesheet. The class vocabulary is small and consistent, so a change
in `css/style.css` reaches all 31 pages — prefer that to per-page markup edits.

Components beyond the basics: `.kicker` (eyebrow), `.lit` (gradient phrase inside a heading),
`.sec-head` + `.label` (section heading), `.tiles`/`.tile` (card with a screenshot),
`.stage` (photo beside copy), `.band` (wide CTA), `.specs`/`.spec` (numbers strip),
`.pills` (link row), `.ticker` (credit marquee), `.spectrum` (hero canvas analyzer).

Mobile drops the nav into a horizontal scroll row. `.nav-toggle` is in the markup on every
page but is hidden by CSS — there is no dropdown menu to maintain.

## Structure

```
/
├── index.html                    # Homepage
├── css/
│   └── style.css                 # Design system (CSS custom properties)
├── js/
│   └── main.js                   # Active nav, card spotlight, hero spectrum canvas
├── images/
│   ├── ls-studio-wide.jpg        # Studio photo, hero/stage blocks
│   ├── ls-portrait.jpg           # Portrait crop, unused spare
│   └── projects/                 # Project screenshots and logos
├── pages/
│   ├── work.html                 # Credentials and expertise
│   ├── projects.html             # Projects hub, grouped by kind
│   ├── live.html                 # The Larry Seyer Show + podcast
│   ├── kits.html                 # Free SFZ drum kits + signup
│   ├── connect.html              # Social and contact links
│   ├── projects/                 # One page per project
│   └── whitepapers/              # Long-form technical documents
└── docs/
    ├── plans/                    # Design and implementation plans
    └── mockups/                  # Design directions (A, B, C). C is the one built.
```

`docs/` is served by GitHub Pages but excluded in `robots.txt`.

## Known Loose Ends

- `pages/projects/tapecolor.html` is an orphan: titled "Vector Tape", superseded by
  `pages/projects/vector-tape.html`. Nothing links to it and it is not in the sitemap.
  Left in place pending a decision to delete it.

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
