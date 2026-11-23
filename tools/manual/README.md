# Larry Seyer Drums beta tester manual

The pages under `pages/projects/larry-seyer-drums-manual/` are generated
from Markdown in this folder. Do not edit the HTML by hand.

    python3 tools/manual/build_manual.py          # write the pages
    python3 tools/manual/build_manual.py --check  # report only; do not write
    python3 tools/manual/build_manual.py --strict # write, but exit 1 on term or price warnings

`--src` defaults to `tools/manual/content`. `--out` defaults to
`pages/projects/larry-seyer-drums-manual`.

The build script has no third-party Python dependencies. A small Markdown
converter lives in `build_manual.py`.

## Local preview

From the repository root, on the `beta-manual-template` branch:

    python3 -m http.server 8000

Then open http://localhost:8000/pages/projects/larry-seyer-drums-manual/

The files are also at:

    /Users/larryseyer/larryseyer.github.io/pages/projects/larry-seyer-drums-manual/index.html

These pages are marked `noindex` and are not linked from any existing site
page until the approved text is in and someone is asked to publish.

## Markdown conventions (for chapter authors)

### Files

- One file per chapter, named `NN-slug.md`, for example `01-welcome.md`.
- `NN` is a two-digit (or longer) zero-padded number and sets chapter order.
- `slug` becomes the public filename (`welcome.html`). Do not rename a file
  once a chapter is linked; change the title in the Markdown instead.
- The landing page is `index.md` and is not a numbered chapter.
- Put images in `tools/manual/content/images/` (see Images below).

### Front matter

Each file starts with YAML-like front matter:

    ---
    title: First launch & getting sound
    summary: Opening Larry Seyer Drums for the first time and hearing sound.
    placeholder: true
    ---

- `title` (required, unless the body starts with a single `#` heading): the
  chapter title shown in the page `<h1>`, the sidebar, search, and prev/next.
  Titles are never hardcoded in the build script.
- `summary` (optional): one sentence used on the contents page and in search.
- `placeholder: true` (optional): adds a visible "Content coming soon" notice.
  Remove this key when the approved chapter text is in.

If `title` is omitted, the first `#` heading in the body is used as the title
and is not repeated in the body.

Do not wrap the title in quotes unless it contains a colon. Apostrophes in
titles may be typed straight (`what's`); the builder turns them into `&rsquo;`.

### Headings and linkable sections

- Do not use `#` (h1) in the body when a front-matter title is present. The
  page already has one h1.
- `##` and `###` become linkable sections. Each gets an id, a heading anchor,
  and a copy-link control. `##` appears in the chapter's sidebar list; `###`
  is nested under the preceding `##`.
- `####` is allowed in the body but is not added to the sidebar.
- Ids are generated from the heading text: lowercased, apostrophes removed,
  other punctuation turned into hyphens, for example `What's included` becomes
  `whats-included`. Duplicates on the same page get `-2`, `-3`, and so on.
- Link to a section with `[text](#whats-included)` on the same page, or
  `[text](03-quick-pick.md#whats-included)` (or `quick-pick.html#whats-included`)
  from another chapter. Links that end in `.md` are rewritten to the built page.

### Writing

- Use typographic apostrophes in the published HTML; type a straight `'` in
  the Markdown and the builder will emit `&rsquo;`. You may also write `&rsquo;`
  yourself.
- A spaced double hyphen (` -- `) becomes an em dash.
- Emphasis: `*italic*` or `_italic_`, `**bold**` or `__bold__`.
- Inline code: `` `like this` ``. Fenced code blocks use triple backticks.
- Lists: `-` or `*` for bullets, `1.` for numbered lists. One level of nesting
  is supported (indent with two or four spaces).
- Block quotes start a line with `>`.
- Tables use the usual pipe form, with a header separator row of dashes.
- Horizontal rules: a line of three or more hyphens.
- Reference-style links (`[text][id]` plus `[id]: url`) and autolinks
  (`<https://example.com>`) are supported.

### Images

- Save files under `tools/manual/content/images/`.
- Prefer web-friendly formats (PNG, JPG, WEBP, GIF, SVG) and names without
  spaces: `images/mixer-overview.png`.
- In Markdown: `![Short alt text](images/mixer-overview.png)`
- Optional visible caption: `![Short alt text](images/mixer-overview.png "The mixer, with the drum channels on the left.")`
- Alt text should describe the image; the builder warns if it is empty.
- The build copies this folder to `pages/projects/larry-seyer-drums-manual/images/`.
- Paths that climb out of the content folder (`../...`) are rejected.

### Site wording

The product is Larry Seyer Drums (Seyer Drums or LSD is fine). Never use the
retired product name; the build script warns if it appears. Do not include
prices (the script also warns on a currency sign followed by a number). Do not
imply that the app is sold or downloaded from this website.

This beta manual has an approved exception to the site-wide trademark rule:
third-party host, format, and product names (for example AUv3 and Ableton Link)
are allowed here. Do not apply that exception to the rest of larryseyer.com.

The retired name is stored only as a hash in `banned_hashes.json`. Use
`--strict` if a warning should fail the build.

### Unsupported Markdown

The converter does not pass through raw HTML (it is escaped), and it does not
support footnotes, definition lists, task-list checkboxes, Math, or Setext
headings under a paragraph (use ATX `#` headings). HTML comments in the
Markdown are stripped and will not appear on the page.

## Files

- `build_manual.py`: reads the Markdown, warns on blocklisted terms, writes
  the HTML pages and `search-index.json`.
- `banned_hashes.json`: hashes of blocklisted terms.
- `content/`: source Markdown and images.
- Generated output (committed, but regenerate after Markdown changes):
  `pages/projects/larry-seyer-drums-manual/*.html`, `search-index.json`.
- Hand-written, not generated: `manual.css`, `manual.js` in that same folder.
