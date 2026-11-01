# Larry Seyer GitHub Pages Website

This repository hosts the personal website for Larry Seyer, served via GitHub Pages at `larryseyer.github.io`.

## Design System

The site uses the **"Precision"** design system (mockup D, Oct 2026), replacing "Stage Light".
It reads like a pro audio plugin / mixing console:

- Dark ground #121418, panels #1a1d22 (#20242a raised), borders #2c3138 / #4a5058
- Text #e9e6df, secondary #a9adb3; accents amber #f0b44c (primary, buttons, `.lit`),
  cyan #6fd6c8, red #e5654e (REC/LED dots, sparingly)
- Instrument Serif (headings, weight 400; `.lit` = italic amber), Familjen Grotesk (body),
  Azeret Mono (labels, kickers, buttons, data)
- Small radii (6–8px), flat plugin-style panels, square-ish amber/outline buttons, no glow or gradients
- Meters/faders only where they fit; all animation stops under prefers-reduced-motion

Every page shares one stylesheet. The class vocabulary is small and consistent, so a change
in `css/style.css` reaches every page — prefer that to per-page markup edits. The
"Precision layer" at the end of the stylesheet holds the overrides and new components.

Components: `.kicker`, `.lit`, `.sec-head` + `.label`, `.tiles`/`.tile`, `.stage`, `.band`,
`.specs`/`.spec`, `.pills`. Home-only: `.fb` (full-bleed studio hero with `.rec` marker and
`#tc` timecode), `.analyzer` (decorative spectrum + credit bands), `[data-meter]` meters,
`.desk`/`.ch` (projects as console channel strips; `.ch--muted` for inactive), `.press-quotes`.
The EmailOctopus embed is skinned via `.inline-container` overrides (with !important).

Mobile (≤1080px): `.nav-toggle` opens a full-height menu (`.header.nav-open`), handled in
`js/main.js` (aria-expanded, closes on link click / Escape).

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
